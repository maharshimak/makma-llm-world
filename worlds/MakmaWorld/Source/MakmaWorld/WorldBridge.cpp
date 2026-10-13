#include "WorldBridge.h"
#include "MakmaCitizen.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

static FVector ReadPosition(const TSharedPtr<FJsonObject>& Object)
{
    return FVector(Object->GetNumberField(TEXT("x")),Object->GetNumberField(TEXT("y")),Object->GetNumberField(TEXT("z")));
}

AWorldBridge::AWorldBridge() { PrimaryActorTick.bCanEverTick=true; }
void AWorldBridge::BeginPlay()
{
    Super::BeginPlay();
    ClientId=FGuid::NewGuid().ToString(EGuidFormats::Digits);
    FetchSnapshot();
}
void AWorldBridge::EndPlay(const EEndPlayReason::Type Reason)
{
    for(auto& Request:PendingRequests) if(Request.IsValid()) Request->CancelRequest();
    PendingRequests.Empty();
    Super::EndPlay(Reason);
}
void AWorldBridge::Tick(float Dt)
{
    Super::Tick(Dt);
    PollElapsed+=Dt;
    if(PollElapsed>=1.f) { PollElapsed=0; FetchSnapshot(); }
    if(GetWorld()->GetTimeSeconds()-LastResponseTime>8.f)
    {
        bConnected=false; ConnectionStatus=TEXT("AI OFFLINE — reconnecting");
        bResynchronize=true;
        for(auto& Entry:Citizens) if(IsValid(Entry.Value)) Entry.Value->PausePhysicalAction();
    }
}
void AWorldBridge::Send(const FString& Path,const TSharedPtr<FJsonObject>& Body,TFunction<void(TSharedPtr<FJsonObject>)> Callback)
{
    auto Request=FHttpModule::Get().CreateRequest();
    Request->SetURL(BaseUrl+Path);Request->SetTimeout(Path==TEXT("/world/conversation")?240.f:5.f);
    Request->SetVerb(Body.IsValid()?TEXT("POST"):TEXT("GET"));
    Request->SetHeader(TEXT("Content-Type"),TEXT("application/json"));
    Request->SetHeader(TEXT("X-Makma-Client"),TEXT("local-console"));
    Request->SetHeader(TEXT("X-Makma-Bridge"),ClientId);
    if(Body.IsValid()) { FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(Body.ToSharedRef(),Writer);Request->SetContentAsString(Text); }
    TWeakObjectPtr<AWorldBridge> WeakThis(this);
    Request->OnProcessRequestComplete().BindLambda([WeakThis,Callback](FHttpRequestPtr Req,FHttpResponsePtr Response,bool bOk)
    {
        if(!WeakThis.IsValid()) return;
        WeakThis->PendingRequests.Remove(Req);
        TSharedPtr<FJsonObject> Parsed;
        if(bOk&&Response.IsValid()&&Response->GetResponseCode()>=200&&Response->GetResponseCode()<300)
        {
            auto Reader=TJsonReaderFactory<>::Create(Response->GetContentAsString());
            if(FJsonSerializer::Deserialize(Reader,Parsed)&&Parsed.IsValid()) { Callback(Parsed);return; }
        }
        Callback(nullptr);
    });
    PendingRequests.Add(Request);Request->ProcessRequest();
}
void AWorldBridge::FetchSnapshot()
{
    if(bRequestInFlight)return;
    bRequestInFlight=true;
    auto Heartbeat=MakeShared<FJsonObject>();Heartbeat->SetNumberField(TEXT("version"),1);Heartbeat->SetStringField(TEXT("client_id"),ClientId);
    if(auto Player=UGameplayStatics::GetPlayerPawn(this,0))
    {
        const FVector Position=Player->GetActorLocation();auto Pos=MakeShared<FJsonObject>();
        Pos->SetNumberField(TEXT("x"),Position.X);Pos->SetNumberField(TEXT("y"),Position.Y);Pos->SetNumberField(TEXT("z"),Position.Z);Heartbeat->SetObjectField(TEXT("player_position"),Pos);
    }
    Send(TEXT("/world/bridge/heartbeat"),Heartbeat,[this](TSharedPtr<FJsonObject> Lease)
    {
        if(!Lease.IsValid()) { bRequestInFlight=false;bConnected=false;return; }
        Send(TEXT("/world/snapshot"),nullptr,[this](TSharedPtr<FJsonObject> State)
        {
            bRequestInFlight=false;
            if(!State.IsValid())return;
            bConnected=true;LastResponseTime=GetWorld()->GetTimeSeconds();ConnectionStatus=TEXT("WORLD ONLINE");
            ApplySnapshot(State);
        });
    });
}
void AWorldBridge::ApplySnapshot(const TSharedPtr<FJsonObject>& State)
{
    if(State->GetIntegerField(TEXT("version"))!=1) { ConnectionStatus=TEXT("INCOMPATIBLE WORLD PROTOCOL");bConnected=false;return; }
    WorldMinutes=State->GetNumberField(TEXT("sim_minutes"));bWorldPaused=State->GetBoolField(TEXT("paused"));
    WorldSpeed=State->GetIntegerField(TEXT("speed"));
    for(const auto& Value:State->GetArrayField(TEXT("citizens")))
    {
        auto Data=Value->AsObject();const FString Id=Data->GetStringField(TEXT("id"));
        AMakmaCitizen* Citizen=Citizens.FindRef(Id);
        if(!IsValid(Citizen))
        {
            FActorSpawnParameters Params;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
            Citizen=GetWorld()->SpawnActor<AMakmaCitizen>(ReadPosition(Data->GetObjectField(TEXT("position"))),FRotator::ZeroRotator,Params);
            if(!Citizen)continue;
            Citizen->AgentId=Id;Citizen->Bridge=this;Citizens.Add(Id,Citizen);
        }
        Citizen->ApplyState(Data);
        if(bResynchronize){Citizen->PausePhysicalAction();Citizen->SetActorLocation(ReadPosition(Data->GetObjectField(TEXT("position"))),false,nullptr,ETeleportType::TeleportPhysics);}
        if(bWorldPaused)Citizen->PausePhysicalAction();
    }
    bResynchronize=false;
    if(bWorldPaused)return;
    for(const auto& Value:State->GetArrayField(TEXT("actions")))
    {
        const auto Data=Value->AsObject();
        if(Data->GetStringField(TEXT("status"))!=TEXT("pending"))continue;
        if(AMakmaCitizen* Citizen=Citizens.FindRef(Data->GetStringField(TEXT("agent_id"))))Citizen->ApplyAction(Data);
    }
}
void AWorldBridge::Report(const FString& AgentId,const FString& ActionId,bool bSuccess,const FVector& Position,const FString& Reason)
{
    auto Body=MakeShared<FJsonObject>();Body->SetNumberField(TEXT("version"),1);Body->SetStringField(TEXT("agent_id"),AgentId);Body->SetStringField(TEXT("action_id"),ActionId);Body->SetStringField(TEXT("event"),bSuccess?TEXT("action_completed"):TEXT("action_failed"));Body->SetStringField(TEXT("reason"),Reason);
    auto Pos=MakeShared<FJsonObject>();Pos->SetNumberField(TEXT("x"),Position.X);Pos->SetNumberField(TEXT("y"),Position.Y);Pos->SetNumberField(TEXT("z"),Position.Z);Body->SetObjectField(TEXT("position"),Pos);
    Send(TEXT("/world/bridge/events"),Body,[this,AgentId](TSharedPtr<FJsonObject> Reply){if(!Reply.IsValid()){ConnectionStatus=TEXT("ACTION ACK FAILED — resynchronizing");if(auto Citizen=Citizens.FindRef(AgentId))Citizen->PausePhysicalAction();}});
}
void AWorldBridge::Talk(const FString& AgentId,const FString& Text)
{
    auto Body=MakeShared<FJsonObject>();Body->SetNumberField(TEXT("version"),1);Body->SetStringField(TEXT("agent_id"),AgentId);Body->SetStringField(TEXT("text"),Text);
    Send(TEXT("/world/conversation"),Body,[this,AgentId](TSharedPtr<FJsonObject> Reply){OnDialogue.Broadcast(AgentId,Reply.IsValid()?Reply->GetStringField(TEXT("reply")):TEXT("AI OFFLINE / conversation unavailable. No response was invented."));});
}
void AWorldBridge::SetClock(bool bPaused,int32 Speed)
{
    auto Body=MakeShared<FJsonObject>();Body->SetNumberField(TEXT("version"),1);Body->SetBoolField(TEXT("paused"),bPaused);Body->SetNumberField(TEXT("speed"),Speed);
    Send(TEXT("/world/clock"),Body,[](TSharedPtr<FJsonObject>){});
}
