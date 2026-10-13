#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MakmaGameMode.generated.h"
class AWorldBridge;
class ADirectionalLight;
UCLASS()
class MAKMAWORLD_API AMakmaGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    AMakmaGameMode();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
private:
    UPROPERTY() TObjectPtr<AWorldBridge> Bridge;
    UPROPERTY() TObjectPtr<ADirectionalLight> Sun;
};
