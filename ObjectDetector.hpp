#pragma once
#include "support/platform.hpp"
#include "support/runtime.hpp"
#include "support/detection.hpp"
#include "support/timing.hpp"
#include "FrameProcessor.hpp"
#include "support/inference_backend.hpp"
#include "support/model_contract.hpp"
class ObjectDetector
{
public:
    ~ObjectDetector();
    HANDLE ActivityEvent() const;
    void NotifyActivity();
    void WaitForActivity(DWORD timeoutMs);

    void Start(const std::wstring& modelPath);

    const std::wstring& ModelPath() const;
    bool Loading() const;
    void WorkerFailed(const char* error) noexcept;
    void WorkerEntry() noexcept;
    void Stop();
    bool Ready()      const;
    bool WantsFrame() const;
    const char* Backend()  const;
    const char* LayoutName() const;
    double InferenceMs()   const;
    std::uint64_t CompletedCount() const;
    LatencyWindow RecentLatency();
    std::string Error();
    std::string BackendDetails();

    void Push(std::vector<float>& tensor, LetterboxInfo lb);

    void EnableSharedInput(ID3D11Device* dev, ID3D11Buffer* first, ID3D11Buffer* second);
    int SharedSlotCount() const;

    bool SharedInput() const;

    void PushShared(LetterboxInfo lb, size_t slot);

    bool CopyLatestIfChanged(std::uint64_t& version, std::vector<Detection>& out, DetectionTiming& timing, BackendStageTiming& stages);

private:
    void MarkFailed() noexcept;

    void SetError(std::string e);

    static float IoU(const Detection& a, const Detection& b);


    struct OutLayout
    {
        int  ch = 0;
        int  anchors = 0;
        bool transposed = false;
        bool objectness = false;
        bool normalized = false;
        bool nms = false;
    };

    static float OutAt(const float* d, const OutLayout& L, int c, int i);

    static OutLayout DetectLayout(const float* d, int d1, int d2, int net);

    static OutLayout ContractLayout(const float* data,int d1,int d2,int net,
        const ModelOutputContract& contract);

    static void SuppressReference(const std::vector<Detection>& cand,
        std::vector<Detection>& keep, std::vector<char>& dead);

    static void SuppressSorted(const std::vector<Detection>& cand,
        std::vector<Detection>& keep, std::vector<char>& dead);

    void Decode(const float* d, int d1, int d2, LetterboxInfo lb);

    void PublishDetections(const LetterboxInfo& lb, double inferenceMs, double decodeMs,
        BackendStageTiming stages={},double workerStarted=0);

    bool WaitForJob(std::vector<float>& local, LetterboxInfo& lb, bool& shared, size_t& slot);

    void LoopGeneric(IInferenceBackend& backend);

    static int ReadNetSize(const WinML::LearningModel& model);

    static int ProbeNetSize(const std::wstring& path);

    void Loop();

    void RecordWinMlError(const char* stage, const winrt::hresult_error& e);

    void LoopWinMl();

    std::wstring            mModelPath;
    std::vector<float>      mInput;
    LetterboxInfo           mLb{};
    std::vector<Detection>  mResults;
    std::vector<Detection>  mDecodeOutput;
    DetectionTiming mResultTiming{};
    LatencyWindow mLatency;
    std::atomic<std::uint64_t> mCompletedCount{ 0 };
    HANDLE mActivityEvent = CreateEventW(nullptr, FALSE, FALSE, nullptr);
    std::uint64_t           mResultVersion = 0;
    std::string             mError;
    BackendStageTiming      mStageTiming{};
    std::string             mBackendDetails;
    std::mutex              mMx, mResMx;
    std::condition_variable mCv;
    std::thread             mWorker;
    std::atomic<bool>       mHasJob{ false }, mQuit{ false }, mReady{ false }, mExited{ true }, mFailed{ false };
    std::atomic<const char*>mBackend{ "none" };
    std::atomic<double>     mInferMs{ 0.0 };
    int                     mNetSize = kNetMax;
    ModelOutputContract mContract{};
    OutLayout               mLayout{};
    int                     mOutD1 = 0, mOutD2 = 0;
    std::vector<Detection>  mCand;
    std::vector<float>      mBestScore;
    std::vector<int>        mBestClass;
    int                     mObjectnessPassed = 0;
    std::vector<char>       mDead;
    ID3D11Device* mSharedDev = nullptr;
    std::array<ID3D11Buffer*, 2> mSharedBuf{};
    std::atomic<int> mSharedSlotCount{ 0 };
    size_t mJobSlot = 0;
    std::atomic<bool>       mSharedReady{ false };
    bool                    mSharedJob = false;
    std::atomic<const char*> mLayoutName{ "?" };
};
