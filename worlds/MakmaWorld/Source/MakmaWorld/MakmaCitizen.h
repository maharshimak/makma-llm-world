#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "MakmaCitizen.generated.h"
class AWorldBridge;
class UTextRenderComponent;
class UStaticMeshComponent;
class FJsonObject;

UCLASS()
class MAKMAWORLD_API AMakmaCitizen : public ACharacter
{
    GENERATED_BODY()
public:
    AMakmaCitizen();
    virtual void Tick(float DeltaTime) override;
    UPROPERTY(BlueprintReadOnly) FString AgentId;
    UPROPERTY(BlueprintReadOnly) FString CitizenName;
    UPROPERTY(BlueprintReadOnly) FString Profession;
    UPROPERTY(BlueprintReadOnly) FString Activity;
    UPROPERTY(BlueprintReadOnly) FString Intention;
    UPROPERTY(BlueprintReadOnly) FString Mood;
    UPROPERTY() TObjectPtr<AWorldBridge> Bridge;
    UPROPERTY() TObjectPtr<UTextRenderComponent> Nameplate;
    void ApplyState(const TSharedPtr<FJsonObject>& State);
    void ApplyAction(const TSharedPtr<FJsonObject>& Action);
    void PausePhysicalAction();
private:
    FString ActiveActionId;
    FVector Target;
    float ActionAge=0;
    float Gait=0;
    bool bNavigating=false;
    bool bReported=false;
    UPROPERTY() TArray<TObjectPtr<UStaticMeshComponent>> Limbs;
};
