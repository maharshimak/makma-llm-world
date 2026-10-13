#include "MakmaGameMode.h"
#include "MakmaPlayer.h"
#include "MakmaHUD.h"
#include "WorldBridge.h"
#include "Engine/DirectionalLight.h"
#include "Components/DirectionalLightComponent.h"
#include "EngineUtils.h"

AMakmaGameMode::AMakmaGameMode()
{
    DefaultPawnClass=AMakmaPlayer::StaticClass();HUDClass=AMakmaHUD::StaticClass();PrimaryActorTick.bCanEverTick=true;
}
void AMakmaGameMode::BeginPlay()
{
    Super::BeginPlay();Bridge=GetWorld()->SpawnActor<AWorldBridge>();
    for(TActorIterator<ADirectionalLight> It(GetWorld());It;++It){Sun=*It;break;}
}
void AMakmaGameMode::Tick(float Dt)
{
    Super::Tick(Dt);
    if(Sun&&Bridge)
    {
        float Hour=FMath::Fmod(Bridge->WorldMinutes/60.f,24.f);
        Sun->SetActorRotation(FRotator((Hour-6.f)*15.f,25.f,0));
        if(auto Light=Cast<UDirectionalLightComponent>(Sun->GetLightComponent()))Light->SetIntensity(Hour>=6&&Hour<=19?3.f:.08f);
    }
}
