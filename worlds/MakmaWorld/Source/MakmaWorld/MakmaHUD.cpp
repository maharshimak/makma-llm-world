#include "MakmaHUD.h"
#include "MakmaCitizen.h"
#include "MakmaPlayer.h"
#include "WorldBridge.h"
#include "Blueprint/WidgetTree.h"
#include "Components/VerticalBox.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "GameFramework/PlayerController.h"
#include "Engine/Canvas.h"

void UMakmaConversationWidget::NativeConstruct()
{
    Super::NativeConstruct();
    if(WidgetTree->RootWidget)return;
    auto CanvasRoot=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());WidgetTree->RootWidget=CanvasRoot;
    auto Border=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass());Border->SetBrushColor(FLinearColor(.025,.045,.055,.97));Border->SetPadding(FMargin(24));
    auto Slot=CanvasRoot->AddChildToCanvas(Border);Slot->SetPosition(FVector2D(35,180));Slot->SetSize(FVector2D(600,390));
    auto Box=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());Border->SetContent(Box);
    Heading=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Box->AddChildToVerticalBox(Heading);
    Response=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Response->SetAutoWrapText(true);Box->AddChildToVerticalBox(Response);
    Input=WidgetTree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass());Input->SetHintText(FText::FromString(TEXT("Ask a question, then press Enter")));Input->OnTextCommitted.AddDynamic(this,&UMakmaConversationWidget::Submit);Box->AddChildToVerticalBox(Input);
    auto Button=WidgetTree->ConstructWidget<UButton>(UButton::StaticClass());auto Label=WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());Label->SetText(FText::FromString(TEXT("Return to world")));Button->AddChild(Label);Button->OnClicked.AddDynamic(this,&UMakmaConversationWidget::Close);Box->AddChildToVerticalBox(Button);
}
void UMakmaConversationWidget::SetCitizen(AMakmaCitizen* Citizen)
{
    CurrentCitizen=Citizen;
    Heading->SetText(FText::FromString(Citizen->CitizenName+TEXT(" — ")+Citizen->Profession));
    Response->SetText(FText::FromString(TEXT("Current activity: ")+Citizen->Activity+TEXT("\nMood: ")+Citizen->Mood+TEXT("\nPrivate memories are not exposed in Citizen Mode.\n")));
    if(Citizen->Bridge){Citizen->Bridge->OnDialogue.RemoveAll(this);Citizen->Bridge->OnDialogue.AddUObject(this,&UMakmaConversationWidget::Reply);}
}
void UMakmaConversationWidget::Submit(const FText& Text,ETextCommit::Type Commit)
{
    if(Commit!=ETextCommit::OnEnter||!CurrentCitizen||!CurrentCitizen->Bridge||Text.IsEmpty())return;
    if(Text.ToString().Len()>1200){Response->SetText(FText::FromString(TEXT("Please keep the question under 1200 characters.")));return;}
    Response->SetText(FText::FromString(TEXT("Waiting for the local model…")));Input->SetIsEnabled(false);CurrentCitizen->Bridge->Talk(CurrentCitizen->AgentId,Text.ToString());
}
void UMakmaConversationWidget::Reply(const FString& AgentId,const FString& Text)
{
    if(CurrentCitizen&&CurrentCitizen->AgentId==AgentId){Response->SetText(FText::FromString(Text));Input->SetIsEnabled(true);Input->SetText(FText::GetEmpty());}
}
void UMakmaConversationWidget::Close()
{
    RemoveFromParent();if(auto PC=GetOwningPlayer()){PC->SetInputMode(FInputModeGameOnly());PC->bShowMouseCursor=false;}
}
void AMakmaHUD::OpenConversation(AMakmaCitizen* Citizen)
{
    if(!Conversation)Conversation=CreateWidget<UMakmaConversationWidget>(GetOwningPlayerController(),UMakmaConversationWidget::StaticClass());
    if(!Conversation->IsInViewport())Conversation->AddToViewport();Conversation->SetCitizen(Citizen);
    GetOwningPlayerController()->bShowMouseCursor=true;GetOwningPlayerController()->SetInputMode(FInputModeGameAndUI());
}
void AMakmaHUD::DrawHUD()
{
    Super::DrawHUD();
    auto Player=Cast<AMakmaPlayer>(GetOwningPawn());if(!Player)return;
    DrawRect(FLinearColor(0.02,0.03,0.04,.85),18,18,650,130);
    DrawText(TEXT("MAK'MA WORLD"),FLinearColor(.55,.9,.8),34,28,nullptr,1.4);
    DrawText(Player->bObserver?TEXT("OBSERVER MODE"):TEXT("CITIZEN MODE"),FLinearColor::White,34,57);
    if(Player->Bridge){int32 Minutes=FMath::FloorToInt(Player->Bridge->WorldMinutes);DrawText(FString::Printf(TEXT("%02d:%02d  |  %s  |  %d citizens"),(Minutes/60)%24,Minutes%60,*Player->Bridge->ConnectionStatus,Player->Bridge->Citizens.Num()),FLinearColor::White,34,78);}
    DrawText(TEXT("WASD Move  |  Shift Sprint  |  E Talk  |  Tab Fly  |  F Follow  |  Esc Cursor"),FLinearColor(.7,.8,.85),34,105);
    if(Player->bDebug&&Player->SelectedCitizen)DrawText(Player->SelectedCitizen->AgentId+TEXT("\n")+Player->SelectedCitizen->Intention,FLinearColor::Yellow,34,160);
    if(Player->Bridge)DrawText(FString::Printf(TEXT("P Pause / resume  |  = Speed: %dx  |  %s"),Player->Bridge->WorldSpeed,Player->Bridge->bWorldPaused?TEXT("PAUSED"):TEXT("RUNNING")),FLinearColor(.7,.8,.85),34,128);
}
