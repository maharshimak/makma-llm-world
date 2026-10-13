#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "MakmaPlayer.generated.h"
class USpringArmComponent;
class UCameraComponent;
class AMakmaCitizen;
class AWorldBridge;
UCLASS()
class MAKMAWORLD_API AMakmaPlayer : public ACharacter
{
    GENERATED_BODY()
public:
    AMakmaPlayer();
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    virtual void Tick(float DeltaTime) override;
    UPROPERTY() TObjectPtr<USpringArmComponent> Boom;
    UPROPERTY() TObjectPtr<UCameraComponent> Camera;
    UPROPERTY() TObjectPtr<AMakmaCitizen> SelectedCitizen;
    UPROPERTY() TObjectPtr<AWorldBridge> Bridge;
    bool bObserver=false;
    bool bDebug=false;
    void Interact();
private:
    bool bFollow=false;
    void Forward(float Value);
    void Right(float Value);
    void Turn(float Value);
    void Look(float Value);
    void Fly(float Value);
    void SprintStart();
    void SprintStop();
    void ToggleObserver();
    void ToggleFollow();
    void ToggleDebug();
    void ReleaseCursor();
    void ToggleClock();
    void CycleSpeed();
};
