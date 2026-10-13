#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/IHttpRequest.h"
#include "WorldBridge.generated.h"

class AMakmaCitizen;
class FJsonObject;
DECLARE_MULTICAST_DELEGATE_TwoParams(FMakmaDialogue, const FString&, const FString&);

UCLASS()
class MAKMAWORLD_API AWorldBridge : public AActor
{
    GENERATED_BODY()
public:
    AWorldBridge();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Tick(float DeltaTime) override;
    UPROPERTY(EditAnywhere, Category="Makma") FString BaseUrl = TEXT("http://127.0.0.1:8765");
    UPROPERTY(BlueprintReadOnly, Category="Makma") bool bConnected = false;
    UPROPERTY(BlueprintReadOnly, Category="Makma") FString ConnectionStatus = TEXT("AI OFFLINE");
    UPROPERTY(BlueprintReadOnly, Category="Makma") float WorldMinutes = 420;
    UPROPERTY(BlueprintReadOnly, Category="Makma") bool bWorldPaused = true;
    UPROPERTY(BlueprintReadOnly, Category="Makma") int32 WorldSpeed = 1;
    UPROPERTY() TMap<FString, TObjectPtr<AMakmaCitizen>> Citizens;
    FMakmaDialogue OnDialogue;
    void Report(const FString& AgentId, const FString& ActionId, bool bSuccess, const FVector& Position, const FString& Reason=TEXT(""));
    void Talk(const FString& AgentId, const FString& Text);
    void SetClock(bool bPaused, int32 Speed);
    void FetchSnapshot();
private:
    FString ClientId;
    float PollElapsed = 0;
    float LastResponseTime = 0;
    bool bRequestInFlight = false;
    bool bResynchronize = true;
    TArray<TSharedPtr<IHttpRequest,ESPMode::ThreadSafe>> PendingRequests;
    void Send(const FString& Path, const TSharedPtr<FJsonObject>& Body, TFunction<void(TSharedPtr<FJsonObject>)> Callback);
    void ApplySnapshot(const TSharedPtr<FJsonObject>& State);
};
