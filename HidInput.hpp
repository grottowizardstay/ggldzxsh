#pragma once

#include "support/platform.hpp"
#include <setupapi.h>
#include <hidsdi.h>

#include <algorithm>
#include <cstdint>
#include <cstring>
#include <cwchar>
#include <cwctype>
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
    explicit HidInput(std::string handshake = {}) : mGreeting(std::move(handshake)) {
        mConnector = std::thread([this] { ConnectorLoop(); });
        mSender = std::thread([this] { SenderLoop(); });
    }
    ~HidInput() {
        { std::lock_guard<std::mutex> lock(mRequestMx); mQuit = true; mWanted = false; mCancelled = true; }
        { std::lock_guard<std::mutex> lock(mQueueMx); mQueueQuit = true; }
        mWake.notify_all(); mQueueWake.notify_all();
        if (mSender.joinable()) mSender.join();
        if (mConnector.joinable()) mConnector.join();
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

    // Blocking sends: each report is written on the calling thread, which waits for the device.
    // A call made while another thread is writing is dropped rather than queued.
    bool SendCommand(uint8_t buttons, int dx, int dy) {
        if (!Connected()) return false;
        std::unique_lock<std::mutex> lock(mIoMx, std::try_to_lock);
        if (!lock || !Connected() || mCancelled.load()) return false;
        if (!SendLocked(buttons, std::clamp(dx, -127, 127), std::clamp(dy, -127, 127))) {
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

    // Non-blocking sends: the caller only records the request and a sender thread writes it.
    // Motion queued while a report is in flight is summed into the next report, button state and
    // motion share a report, and nothing is dropped because another thread is sending.
    // They return false only when the device is not connected. If a write fails, whatever is
    // still queued is discarded so stale motion is not replayed after a reconnect.
    bool QueueMove(int dx, int dy) {
        if (!QueueReady()) return false;
        { std::lock_guard<std::mutex> lock(mQueueMx); mQueuedX += dx; mQueuedY += dy; }
        mQueueWake.notify_one(); return true;
    }
    // Sets the buttons held from the next report on.
    bool QueueButtons(uint8_t buttons) {
        if (!QueueReady()) return false;
        { std::lock_guard<std::mutex> lock(mQueueMx); mQueuedButtons = buttons; mButtonsDirty = true; }
        mQueueWake.notify_one(); return true;
    }
    // Presses the left button and releases it holdMs later without blocking the caller.
    bool QueueClick(unsigned holdMs = 25) {
        if (!QueueReady()) return false;
        { std::lock_guard<std::mutex> lock(mQueueMx); ++mQueuedClicks; mClickHoldMs = holdMs; }
        mQueueWake.notify_one(); return true;
    }
    // Waits until everything queued has been written or discarded.
    bool Flush(unsigned timeoutMs = 1000) {
        std::unique_lock<std::mutex> lock(mQueueMx);
        return mQueueIdle.wait_for(lock, std::chrono::milliseconds(timeoutMs),
            [this] { return !mSenderBusy && !QueuedLocked(); });
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
    // Writes one report. Requires mIoMx; x and y must already be within +-127.
    bool SendLocked(uint8_t buttons, int x, int y) {
        // Bytes past the fourth stay zero from OpenPreferred, so the report is not cleared per send.
        auto& packet = mPacket;
        packet[1] = buttons; packet[2] = uint8_t(int8_t(x)); packet[3] = uint8_t(int8_t(y));
        const auto t0 = DevHidTimeUs();
        const auto result = vision::Write(mDevice, packet.data(), DWORD(packet.size()), 100, &mCancelled);
        const auto t1 = DevHidTimeUs();
        const bool shortWrite = result.ok && result.bytes != packet.size();
        const bool complete = result.ok && !shortWrite;
        gDevHid.Record(t1 >= t0 ? t1 - t0 : 0, complete, shortWrite,
            shortWrite ? ERROR_WRITE_FAULT : result.error);
        if (!complete) { SetStatus(L"Write failed / incomplete"); DisconnectLocked(); }
        return complete;
    }
    bool QueueReady() {
        if (Connected()) return true;
        RequestReconnect(); gDevHid.dropped.fetch_add(1, std::memory_order_relaxed); return false;
    }
    bool QueuedLocked() const noexcept { return mQueuedX || mQueuedY || mButtonsDirty || mQueuedClicks; }
    void SenderLoop() noexcept {
        vision::GuardWorker([this] {
            using Clock = std::chrono::steady_clock;
            std::unique_lock<std::mutex> queue(mQueueMx);
            bool clicking = false; Clock::time_point releaseAt{};
            for (;;) {
                for (;;) {
                    if (mQueueQuit) return;
                    if (mQueuedX || mQueuedY || mButtonsDirty) break;
                    if (clicking ? Clock::now() >= releaseAt : mQueuedClicks > 0) break;
                    if (clicking) mQueueWake.wait_until(queue, releaseAt);
                    else { mSenderBusy = false; mQueueIdle.notify_all(); mQueueWake.wait(queue); }
                }
                mSenderBusy = true;
                bool pressed = false;
                // A release always gets its own report, so back-to-back clicks stay distinct.
                if (clicking) { if (Clock::now() >= releaseAt) { clicking = false; --mQueuedClicks; } }
                else if (mQueuedClicks > 0) { clicking = pressed = true; }
                mButtonsDirty = false;
                const uint8_t buttons = uint8_t(mQueuedButtons | (clicking ? kButtonLeft : 0));
                const int x = int(std::clamp<long long>(mQueuedX, -127, 127)), y = int(std::clamp<long long>(mQueuedY, -127, 127));
                mQueuedX -= x; mQueuedY -= y;
                const unsigned holdMs = mClickHoldMs;
                queue.unlock();
                bool ok = false;
                if (Connected()) {
                    std::lock_guard<std::mutex> io(mIoMx);
                    ok = Connected() && !mCancelled.load() && SendLocked(buttons, x, y);
                }
                if (!ok) RequestReconnect();
                queue.lock();
                if (!ok) {
                    gDevHid.dropped.fetch_add(1, std::memory_order_relaxed);
                    mQueuedX = mQueuedY = 0; mQueuedClicks = 0; mQueuedButtons = 0; mButtonsDirty = false; clicking = false;
                }
                else if (pressed) releaseAt = Clock::now() + std::chrono::milliseconds(holdMs);
            }
        }, [this](const char*) {
            SetStatus(L"Device worker failed; restart application");
        }, [] {});
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
    struct Candidate { const wchar_t* name; USHORT pid; };
    static constexpr Candidate kCandidates[2] = {{L"Leonardo", kPidLeonardo}, {L"Micro", kPidMicro}};
    void ConnectLocked() {
        DisconnectLocked();
        const int found = mCancelled.load() ? -1 : OpenPreferred();
        if (found < 0) { SetStatus(L"Not found (retry in 2 seconds)"); return; }
        const auto& c = kCandidates[found];
        bool handshake = false;
        try { handshake = TestConnection(); }
        catch (...) { DisconnectLocked(); throw; }
        if (mCancelled.load()) { DisconnectLocked(); return; }
        { std::lock_guard<std::mutex> status(mStatusMx); mDeviceName = c.name; mStatus = mDeviceName + (handshake ? L" (RawHID)" : L" (no handshake response)"); }
        mHandshake = handshake; mConnected.store(true, std::memory_order_release);
        gDevHid.connects.fetch_add(1); gDevHid.reconnects.fetch_add(1);
        gDevHid.connected = 1; gDevHid.handshake = handshake ? 1 : 0; gDevHid.reportBytes = mReportLength;
        DevLog("HID", handshake ? "Connected, handshake OK" : "Connected, no handshake response");
    }
    // Which candidates an interface path can belong to, as a bit mask. USB HID paths carry
    // "vid_xxxx&pid_xxxx", which rules out other devices without opening them; a path without
    // that tag is kept for both candidates.
    static unsigned PathCandidates(const wchar_t* path) {
        std::wstring lower(path);
        for (auto& ch : lower) ch = wchar_t(std::towlower(ch));
        if (lower.find(L"vid_") == std::wstring::npos) return 3u;
        unsigned mask = 0;
        for (unsigned i = 0; i < 2; ++i) {
            wchar_t tag[32];
            swprintf(tag, 32, L"vid_%04x&pid_%04x", unsigned(kVendorId), unsigned(kCandidates[i].pid));
            if (lower.find(tag) != std::wstring::npos) mask |= 1u << i;
        }
        return mask;
    }
    // Enumerates the HID interfaces once for both boards and opens the first RawHID match,
    // preferring the Leonardo. Returns the index into kCandidates, or -1.
    int OpenPreferred() {
        GUID hidGuid{};
        HidD_GetHidGuid(&hidGuid);

        HDEVINFO info = SetupDiGetClassDevsW(&hidGuid, nullptr, nullptr,
            DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
        if (info == INVALID_HANDLE_VALUE) {
            return -1;
        }

        std::vector<std::wstring> paths[2];
        {
            struct InfoLease { HDEVINFO value; ~InfoLease() { SetupDiDestroyDeviceInfoList(value); } } lease{info};
            SP_DEVICE_INTERFACE_DATA iface{};
            iface.cbSize = sizeof(iface);
            std::vector<uint8_t> buffer;
            for (DWORD index = 0; SetupDiEnumDeviceInterfaces(info, nullptr, &hidGuid, index, &iface); ++index)
            {
                DWORD required = 0;
                SetupDiGetDeviceInterfaceDetailW(info, &iface, nullptr, 0, &required, nullptr);
                if (required == 0) {
                    continue;
                }
                if (buffer.size() < required) buffer.resize(required);
                auto* detail = reinterpret_cast<PSP_DEVICE_INTERFACE_DETAIL_DATA_W>(buffer.data());
                detail->cbSize = sizeof(SP_DEVICE_INTERFACE_DETAIL_DATA_W);
                if (!SetupDiGetDeviceInterfaceDetailW(info, &iface, detail, required, nullptr, nullptr)) {
                    continue;
                }
                const unsigned mask = PathCandidates(detail->DevicePath);
                for (unsigned i = 0; i < 2; ++i) if (mask & (1u << i)) paths[i].emplace_back(detail->DevicePath);
            }
        }

        for (int i = 0; i < 2; ++i) for (const auto& path : paths[i])
        {
            if (mCancelled.load()) return -1;
            HANDLE device = CreateFileW(path.c_str(),
                GENERIC_READ | GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                nullptr, OPEN_EXISTING, FILE_FLAG_OVERLAPPED, nullptr);
            if (device == INVALID_HANDLE_VALUE) {
                continue;
            }

            if (MatchesRawHid(device, kCandidates[i].pid)) {
                vision::Handle candidate(device);
                mPacket.assign(mReportLength, 0);
                mDevice = candidate.Release();
                return i;
            }
            CloseHandle(device);
        }
        return -1;
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
    // Queue for the non-blocking sends, guarded by mQueueMx.
    std::mutex mQueueMx;
    std::condition_variable mQueueWake, mQueueIdle;
    long long mQueuedX = 0, mQueuedY = 0;
    int mQueuedClicks = 0;
    unsigned mClickHoldMs = 25;
    uint8_t mQueuedButtons = 0;
    bool mButtonsDirty = false, mSenderBusy = false, mQueueQuit = false;
    std::thread mConnector, mSender;
};
