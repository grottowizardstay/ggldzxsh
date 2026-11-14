#pragma once

#include "support/platform.hpp"
#include <setupapi.h>
#include <hidsdi.h>

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <chrono>
#include <mutex>
#include <atomic>
#include <condition_variable>
#include <thread>
#include "support/overlapped_io.hpp"
#include "support/worker_guard.hpp"
#include "support/diagnostics.hpp"

#pragma comment(lib, "hid.lib")
#pragma comment(lib, "setupapi.lib")

struct DevHidCounters {
    std::atomic<unsigned long long> writes{0}, failures{0}, shortWrites{0}, dropped{0};
    std::atomic<unsigned long long> totalUs{0}, maxUs{0}, reconnects{0}, connects{0}, disconnects{0};
    std::atomic<unsigned long> lastError{0};
    std::atomic<int> connected{0}, handshake{0}, reportBytes{0};
    void Record(unsigned long long us, bool ok, bool shortWrite, unsigned long err) noexcept {
        writes.fetch_add(1, std::memory_order_relaxed);
        totalUs.fetch_add(us, std::memory_order_relaxed);
        if (!ok) { failures.fetch_add(1, std::memory_order_relaxed); lastError.store(err, std::memory_order_relaxed); }
        if (shortWrite) shortWrites.fetch_add(1, std::memory_order_relaxed);
        auto prev = maxUs.load(std::memory_order_relaxed);
        while (prev < us && !maxUs.compare_exchange_weak(prev, us, std::memory_order_relaxed)) {}
    }
};
inline DevHidCounters gDevHid;
inline unsigned long long DevHidTimeUs() noexcept {
    static const double factor = [] { LARGE_INTEGER f{}; return QueryPerformanceFrequency(&f) && f.QuadPart > 0 ? 1000000.0 / double(f.QuadPart) : 0.0; }();
    LARGE_INTEGER t{}; QueryPerformanceCounter(&t);
    return static_cast<unsigned long long>(double(t.QuadPart) * factor);
}

class HidInput {
public:
    static constexpr USHORT kVendorId = 0x2341, kPidLeonardo = 0x8036, kPidMicro = 0x8037;
    static constexpr USHORT kUsagePage = 0xFFC0, kUsage = 0x0C00;
    static constexpr uint8_t kButtonLeft = 1, kButtonRight = 2, kButtonMiddle = 4;
    explicit HidInput(std::string handshake = {}) : mGreeting(std::move(handshake)) { mConnector = std::thread([this] { ConnectorLoop(); }); }
    ~HidInput() {
        { std::lock_guard<std::mutex> lock(mRequestMx); mQuit = true; mWanted = false; mCancelled = true; }
        mWake.notify_all(); if (mConnector.joinable()) mConnector.join();
        std::lock_guard<std::mutex> lock(mIoMx); DisconnectLocked();
    }
    HidInput(const HidInput&) = delete;
    HidInput& operator=(const HidInput&) = delete;
    bool Connected() const noexcept { return mConnected.load(std::memory_order_acquire); }
    bool Handshaked() const noexcept { return mHandshake.load(std::memory_order_acquire); }
    std::wstring DeviceName() const { std::lock_guard<std::mutex> lock(mStatusMx); return mDeviceName; }
    std::wstring Status() const { std::lock_guard<std::mutex> lock(mStatusMx); return mStatus; }

    bool Connect() {
        { std::lock_guard<std::mutex> lock(mRequestMx); if (mQuit) return false; mWanted = true; mRequested = true; }
        SetStatus(L"Connecting..."); mWake.notify_one(); return true;
    }
    void Disconnect() noexcept {
        { std::lock_guard<std::mutex> lock(mRequestMx); mWanted = false; mRequested = true; mCancelled = true; }
        mConnected = false; mWake.notify_one();
    }
    bool SendCommand(uint8_t buttons, int dx, int dy) {
        if (!Connected()) return false;
        std::unique_lock<std::mutex> lock(mIoMx, std::try_to_lock);
        if (!lock || !Connected() || mCancelled.load()) return false;
        auto& packet = mPacket; std::fill(packet.begin(), packet.end(), uint8_t(0));
        packet[0] = 0; packet[1] = buttons;
        packet[2] = uint8_t(int8_t(std::clamp(dx, -127, 127)));
        packet[3] = uint8_t(int8_t(std::clamp(dy, -127, 127)));
        const auto t0 = DevHidTimeUs();
        const auto result = vision::Write(mDevice, packet.data(), DWORD(packet.size()), 100, &mCancelled);
        const auto t1 = DevHidTimeUs();
        const bool shortWrite = result.ok && result.bytes != packet.size();
        const bool complete = result.ok && !shortWrite;
        gDevHid.Record(t1 >= t0 ? t1 - t0 : 0, complete, shortWrite,
            shortWrite ? ERROR_WRITE_FAULT : result.error);
        if (!complete) {
            SetStatus(L"Write failed / incomplete"); DisconnectLocked();
            lock.unlock(); RequestReconnect(); return false;
        }
        return true;
    }
    bool MoveRelative(int dx, int dy) {
        if (!Connected()) { RequestReconnect(); gDevHid.dropped.fetch_add(1); return false; }
        while (dx || dy) {
            const int x = std::clamp(dx, -127, 127), y = std::clamp(dy, -127, 127);
            if (!SendCommand(0, x, y)) { gDevHid.dropped.fetch_add(1); return false; }
            dx -= x; dy -= y;
        }
        return true;
    }
    bool Click(unsigned holdMs = 25) {
        if (!SendCommand(kButtonLeft, 0, 0)) return false;
        Sleep(holdMs); return SendCommand(0, 0, 0);
    }
private:
    void SetStatus(const std::wstring& value) { std::lock_guard<std::mutex> lock(mStatusMx); mStatus = value; }
    void DisconnectLocked() noexcept {
        mConnected = false; mHandshake = false;
        if (mDevice != INVALID_HANDLE_VALUE) { CloseHandle(mDevice); mDevice = INVALID_HANDLE_VALUE; gDevHid.disconnects.fetch_add(1); }
        gDevHid.connected = 0; gDevHid.handshake = 0;
    }
    void RequestReconnect() {
        { std::lock_guard<std::mutex> lock(mRequestMx); }
        mWake.notify_one();
    }
    void ConnectorLoop() noexcept {
        vision::GuardWorker([this] {
            std::unique_lock<std::mutex> request(mRequestMx);
            for (;;) {
                mWake.wait_for(request, std::chrono::milliseconds(2000),
                    [this] { return mQuit || mRequested || (mWanted && !mConnected.load()); });
                if (!mQuit && !mRequested && !(mWanted && !mConnected.load())) continue;
                if (mQuit) return;
                const bool wanted = mWanted; mRequested = false;
                if (wanted) mCancelled = false;
                request.unlock();
                { std::lock_guard<std::mutex> io(mIoMx);
                  if (!wanted) { DisconnectLocked(); SetStatus(L"Disconnected"); }
                  else if (!Connected()) ConnectLocked(); }
                request.lock();
                if (mQuit) return;
                if (mWanted && !Connected()) mWake.wait_for(request, std::chrono::milliseconds(2000),
                    [this] { return mQuit || mRequested || !mWanted; });
            }
        }, [this](const char*) {
            mConnected = false; SetStatus(L"Device worker failed; restart application");
        }, [] {});
    }
    void ConnectLocked() {
        DisconnectLocked();
        const struct { const wchar_t* name; USHORT pid; } candidates[] = {{L"Leonardo", kPidLeonardo}, {L"Micro", kPidMicro}};
        for (const auto& c : candidates) {
            if (mCancelled.load() || !OpenByPid(c.pid)) continue;
            bool handshake = false;
            try { handshake = TestConnection(); }
            catch (...) { DisconnectLocked(); throw; }
            if (mCancelled.load()) { DisconnectLocked(); return; }
            { std::lock_guard<std::mutex> status(mStatusMx); mDeviceName = c.name; mStatus = mDeviceName + (handshake ? L" (RawHID)" : L" (no handshake response)"); }
            mHandshake = handshake; mConnected.store(true, std::memory_order_release);
            gDevHid.connects.fetch_add(1); gDevHid.reconnects.fetch_add(1);
            gDevHid.connected = 1; gDevHid.handshake = handshake ? 1 : 0; gDevHid.reportBytes = mReportLength;
            DevLog("HID", handshake ? "Connected, handshake OK" : "Connected, no handshake response"); return;
        }
        SetStatus(L"Not found (retry in 2 seconds)");
    }
    bool OpenByPid(USHORT pid) {
        GUID hidGuid{};
        HidD_GetHidGuid(&hidGuid);

        HDEVINFO info = SetupDiGetClassDevsW(&hidGuid, nullptr, nullptr,
            DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
        if (info == INVALID_HANDLE_VALUE) {
            return false;
        }

        struct InfoLease { HDEVINFO value; ~InfoLease() { SetupDiDestroyDeviceInfoList(value); } } lease{info};
        bool opened = false;
        SP_DEVICE_INTERFACE_DATA iface{};
        iface.cbSize = sizeof(iface);

        for (DWORD index = 0;
             !opened && SetupDiEnumDeviceInterfaces(info, nullptr, &hidGuid, index, &iface);
             ++index)
        {
            DWORD required = 0;
            SetupDiGetDeviceInterfaceDetailW(info, &iface, nullptr, 0, &required, nullptr);
            if (required == 0) {
                continue;
            }

            std::vector<uint8_t> buffer(required);
            auto* detail = reinterpret_cast<PSP_DEVICE_INTERFACE_DETAIL_DATA_W>(buffer.data());
            detail->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_W);
            if (!SetupDiGetDeviceInterfaceDetailW(info, &iface, detail, required, nullptr, nullptr)) {
                continue;
            }

            HANDLE device = CreateFileW(detail->DevicePath,
                GENERIC_READ | GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                nullptr, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, nullptr);
            if (device == INVALID_HANDLE_VALUE) {
                continue;
            }

            if (MatchesRawHid(device, pid)) {
                vision::Handle candidate(device);
                mPacket.assign(mReportLength, 0);
                mDevice = candidate.Release();
                opened = true;
                break;
            }
            CloseHandle(device);
        }

        return opened;
    }
    bool MatchesRawHid(HANDLE device, USHORT pid) {
        HIDD_ATTRIBUTES attrs{};
        attrs.Size = sizeof(attrs);
        if (!HidD_GetAttributes(device, &attrs)) {
            return false;
        }
        if (attrs.VendorID != kVendorId || attrs.ProductID != pid) {
            return false;
        }

        PHIDP_PREPARSED_DATA preparsed = nullptr;
        if (!HidD_GetPreparsedData(device, &preparsed)) {
            return false;
        }

        HIDP_CAPS caps{};
        const bool ok = HidP_GetCaps(preparsed, &caps) == HIDP_STATUS_SUCCESS
            && caps.UsagePage == kUsagePage
            && caps.Usage == kUsage;
        if (ok && caps.OutputReportByteLength >= 4 && caps.OutputReportByteLength <= 16384
            && caps.InputReportByteLength <= 16384) {
            mReportLength = caps.OutputReportByteLength > 0 ? caps.OutputReportByteLength : 65;
            mInputLength = caps.InputReportByteLength > 0 ? caps.InputReportByteLength : 65;
        }
        HidD_FreePreparsedData(preparsed);
        return ok && caps.OutputReportByteLength >= 4 && caps.OutputReportByteLength <= 16384
            && caps.InputReportByteLength <= 16384;
    }

    bool TestConnection() {
        if (mDevice == INVALID_HANDLE_VALUE || mCancelled.load()) return false;
        const ULONGLONG begin = GetTickCount64();
        std::vector<uint8_t> packet(mReportLength, 0);
        if (mGreeting.empty()) return false;
        const auto& hello = mGreeting;
        for (size_t i = 0; i < hello.size() && i + 1 < packet.size(); ++i) packet[i + 1] = uint8_t(hello[i]);
        const auto sent = vision::Write(mDevice, packet.data(), DWORD(packet.size()), 200, &mCancelled);
        if (!sent.ok || sent.bytes != packet.size()) return false;
        std::vector<uint8_t> reply(mInputLength, 0);
        while (!mCancelled.load() && GetTickCount64() - begin < 2000) {
            const DWORD remaining = DWORD(2000 - (GetTickCount64() - begin));
            if (!remaining || remaining > 2000) break;
            const auto received = vision::Read(mDevice, reply.data(), DWORD(reply.size()), (std::min<DWORD>)(remaining, 100), &mCancelled);
            if (received.ok && received.bytes && std::string(reinterpret_cast<const char*>(reply.data()), received.bytes).find("OK") != std::string::npos) return true;
        }
        return false;
    }
    const std::string mGreeting;
    HANDLE mDevice = INVALID_HANDLE_VALUE;
    USHORT mReportLength = 65, mInputLength = 65;
    std::vector<uint8_t> mPacket;
    std::atomic<bool> mConnected{false}, mHandshake{false}, mCancelled{false};
    std::mutex mIoMx, mRequestMx;
    mutable std::mutex mStatusMx;
    std::condition_variable mWake;
    bool mQuit = false, mWanted = false, mRequested = false;
    std::wstring mDeviceName, mStatus = L"Disconnected";
    std::thread mConnector;
};
