#include "MakmaCitizen.h"
#include "WorldBridge.h"
#include "AIController.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Dom/JsonObject.h"
#include "UObject/ConstructorHelpers.h"

AMakmaCitizen::AMakmaCitizen()
{
    PrimaryActorTick.bCanEverTick=true;AIControllerClass=AAIController::StaticClass();AutoPossessAI=EAutoPossessAI::PlacedInWorldOrSpawned;
    GetCapsuleComponent()->InitCapsuleSize(32,88);GetCharacterMovement()->MaxWalkSpeed=140;GetCharacterMovement()->bOrientRotationToMovement=true;bUseControllerRotationYaw=false;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    auto Torso=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Torso"));Torso->SetupAttachment(GetRootComponent());Torso->SetStaticMesh(Cylinder.Object);Torso->SetRelativeLocation(FVector(0,0,5));Torso->SetRelativeScale3D(FVector(.38,.28,.6));Torso->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    auto Head=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Head"));Head->SetupAttachment(GetRootComponent());Head->SetStaticMesh(Sphere.Object);Head->SetRelativeLocation(FVector(0,0,57));Head->SetRelativeScale3D(FVector(.28));Head->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    for(int32 I=0;I<4;I++) { auto Part=CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("Limb%d"),I));Part->SetupAttachment(GetRootComponent());Part->SetStaticMesh(Cylinder.Object);Part->SetRelativeLocation(FVector(0,(I%2==0?-1:1)*(I<2?27:12),I<2?0:-54));Part->SetRelativeScale3D(FVector(.12,.12,I<2?.55:.60));Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);Limbs.Add(Part); }
    Nameplate=CreateDefaultSubobject<UTextRenderComponent>(TEXT("Nameplate"));Nameplate->SetupAttachment(GetRootComponent());Nameplate->SetRelativeLocation(FVector(0,0,115));Nameplate->SetWorldSize(17);Nameplate->SetHorizontalAlignment(EHTA_Center);
}
void AMakmaCitizen::ApplyState(const TSharedPtr<FJsonObject>& State)
{
    CitizenName=State->GetStringField(TEXT("name"));Profession=State->GetStringField(TEXT("profession"));Activity=State->GetStringField(TEXT("activity"));Intention=State->GetStringField(TEXT("intention"));Mood=State->GetStringField(TEXT("mood"));
    Nameplate->SetText(FText::FromString(CitizenName+TEXT("\n")+Activity));
    FString StateActionId;State->TryGetStringField(TEXT("action_id"),StateActionId);
    if(StateActionId!=ActiveActionId){PausePhysicalAction();ActiveActionId.Empty();}
}
void AMakmaCitizen::ApplyAction(const TSharedPtr<FJsonObject>& Action)
{
    FString Id=Action->GetStringField(TEXT("id"));if(Id==ActiveActionId&&(bNavigating||bReported))return;
    ActiveActionId=Id;bReported=false;ActionAge=0;
    auto Pos=Action->GetObjectField(TEXT("position"));Target=FVector(Pos->GetNumberField(TEXT("x")),Pos->GetNumberField(TEXT("y")),Pos->GetNumberField(TEXT("z")));
    AAIController* AI=Cast<AAIController>(GetController());
    if(!AI) { SpawnDefaultController();AI=Cast<AAIController>(GetController()); }
    if(!AI) { Bridge->Report(AgentId,Id,false,GetActorLocation(),TEXT("No navigation controller"));bReported=true;return; }
    const auto Result=AI->MoveToLocation(Target,65.f,true,true,false,true,nullptr,false);
    if(Result==EPathFollowingRequestResult::Failed) { Bridge->Report(AgentId,Id,false,GetActorLocation(),TEXT("NavMesh has no valid route"));bReported=true; }
    else bNavigating=true;
}
void AMakmaCitizen::PausePhysicalAction()
{
    if(auto AI=Cast<AAIController>(GetController()))AI->StopMovement();
    bNavigating=false;bReported=false;
}
void AMakmaCitizen::Tick(float Dt)
{
    Super::Tick(Dt);
    float Speed=GetVelocity().Size2D();Gait+=Dt*Speed*.035;
    for(int32 I=0;I<Limbs.Num();I++)Limbs[I]->SetRelativeRotation(FRotator(Speed>5?FMath::Sin(Gait+(I%2?PI:0))*(I<2?20:25):0,0,0));
    if(bNavigating&&Bridge&&Bridge->bConnected)
    {
        ActionAge+=Dt;
        if(FVector::Dist2D(GetActorLocation(),Target)<100) { bNavigating=false;bReported=true;Bridge->Report(AgentId,ActiveActionId,true,GetActorLocation()); }
        else if(ActionAge>90) { PausePhysicalAction();bReported=true;Bridge->Report(AgentId,ActiveActionId,false,GetActorLocation(),TEXT("Navigation timed out")); }
    }
}
