#include "MakmaPlayer.h"
#include "MakmaCitizen.h"
#include "WorldBridge.h"
#include "MakmaHUD.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InputComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "EngineUtils.h"

AMakmaPlayer::AMakmaPlayer()
{
    PrimaryActorTick.bCanEverTick=true;
    GetCharacterMovement()->MaxWalkSpeed=400;GetCharacterMovement()->bOrientRotationToMovement=true;bUseControllerRotationYaw=false;
    Boom=CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));Boom->SetupAttachment(GetRootComponent());Boom->TargetArmLength=420;Boom->bUsePawnControlRotation=true;
    Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));Camera->SetupAttachment(Boom);
    auto Body=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlayerBody"));Body->SetupAttachment(GetRootComponent());
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Capsule(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));Body->SetStaticMesh(Capsule.Object);Body->SetRelativeScale3D(FVector(.5,.5,1.65));Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
void AMakmaPlayer::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAction(TEXT("ToggleClock"),IE_Pressed,this,&AMakmaPlayer::ToggleClock);Input->BindAction(TEXT("CycleSpeed"),IE_Pressed,this,&AMakmaPlayer::CycleSpeed);
    Input->BindAxis(TEXT("MoveForward"),this,&AMakmaPlayer::Forward);Input->BindAxis(TEXT("MoveRight"),this,&AMakmaPlayer::Right);Input->BindAxis(TEXT("Turn"),this,&AMakmaPlayer::Turn);Input->BindAxis(TEXT("LookUp"),this,&AMakmaPlayer::Look);Input->BindAxis(TEXT("FlyUp"),this,&AMakmaPlayer::Fly);
    Input->BindAction(TEXT("Sprint"),IE_Pressed,this,&AMakmaPlayer::SprintStart);Input->BindAction(TEXT("Sprint"),IE_Released,this,&AMakmaPlayer::SprintStop);Input->BindAction(TEXT("Interact"),IE_Pressed,this,&AMakmaPlayer::Interact);Input->BindAction(TEXT("Observer"),IE_Pressed,this,&AMakmaPlayer::ToggleObserver);Input->BindAction(TEXT("Follow"),IE_Pressed,this,&AMakmaPlayer::ToggleFollow);Input->BindAction(TEXT("ToggleDebug"),IE_Pressed,this,&AMakmaPlayer::ToggleDebug);Input->BindAction(TEXT("ReleaseCursor"),IE_Pressed,this,&AMakmaPlayer::ReleaseCursor);
}
void AMakmaPlayer::Forward(float V) {if(Controller&&V!=0){bFollow=false;AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::X),V);}}
void AMakmaPlayer::Right(float V) {if(Controller&&V!=0){bFollow=false;AddMovementInput(FRotationMatrix(FRotator(0,Controller->GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),V);}}
void AMakmaPlayer::Turn(float V){AddControllerYawInput(V);}
void AMakmaPlayer::Look(float V){AddControllerPitchInput(V);}
void AMakmaPlayer::Fly(float V){if(bObserver)AddMovementInput(FVector::UpVector,V);}
void AMakmaPlayer::SprintStart(){GetCharacterMovement()->MaxWalkSpeed=700;}
void AMakmaPlayer::SprintStop(){GetCharacterMovement()->MaxWalkSpeed=400;}
void AMakmaPlayer::ToggleObserver(){bObserver=!bObserver;GetCharacterMovement()->SetMovementMode(bObserver?MOVE_Flying:MOVE_Walking);Boom->TargetArmLength=bObserver?800:420;}
void AMakmaPlayer::ToggleFollow(){if(SelectedCitizen){if(!bObserver)ToggleObserver();bFollow=!bFollow;}}
void AMakmaPlayer::ToggleDebug(){bDebug=!bDebug;}
void AMakmaPlayer::ToggleClock(){if(Bridge)Bridge->SetClock(!Bridge->bWorldPaused,Bridge->WorldSpeed);}
void AMakmaPlayer::CycleSpeed(){if(Bridge){const int32 Speed=Bridge->WorldSpeed;Bridge->SetClock(Bridge->bWorldPaused,Speed==1?5:Speed==5?10:Speed==10?20:Speed==20?100:1);}}
void AMakmaPlayer::ReleaseCursor(){if(auto PC=Cast<APlayerController>(Controller)){PC->bShowMouseCursor=!PC->bShowMouseCursor;if(PC->bShowMouseCursor)PC->SetInputMode(FInputModeGameAndUI());else PC->SetInputMode(FInputModeGameOnly());}}
void AMakmaPlayer::Interact()
{
    AMakmaCitizen* Nearest=nullptr;float Best=bObserver?2000:350;
    for(TActorIterator<AMakmaCitizen> It(GetWorld());It;++It){float D=FVector::Dist(GetActorLocation(),It->GetActorLocation());if(D<Best){Best=D;Nearest=*It;}}
    if(Nearest){SelectedCitizen=Nearest;if(auto PC=Cast<APlayerController>(Controller))if(auto HUD=Cast<AMakmaHUD>(PC->GetHUD()))HUD->OpenConversation(Nearest);}
}
void AMakmaPlayer::Tick(float Dt)
{
    Super::Tick(Dt);
    if(!Bridge)for(TActorIterator<AWorldBridge> It(GetWorld());It;++It){Bridge=*It;break;}
    if(bFollow&&SelectedCitizen)SetActorLocation(FMath::VInterpTo(GetActorLocation(),SelectedCitizen->GetActorLocation()+FVector(-400,0,300),Dt,2),true);
}
