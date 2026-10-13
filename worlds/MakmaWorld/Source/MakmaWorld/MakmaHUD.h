#pragma once
#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "Blueprint/UserWidget.h"
#include "Components/EditableTextBox.h"
#include "MakmaHUD.generated.h"
class AMakmaCitizen;
class UTextBlock;
class UButton;
class AWorldBridge;

UCLASS()
class MAKMAWORLD_API UMakmaConversationWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    virtual void NativeConstruct() override;
    void SetCitizen(AMakmaCitizen* Citizen);
    void Reply(const FString& AgentId,const FString& Text);
    UPROPERTY() TObjectPtr<UTextBlock> Heading;
    UPROPERTY() TObjectPtr<UTextBlock> Response;
    UPROPERTY() TObjectPtr<UEditableTextBox> Input;
    UPROPERTY() TObjectPtr<AMakmaCitizen> CurrentCitizen;
    UFUNCTION() void Submit(const FText& Text,ETextCommit::Type Commit);
    UFUNCTION() void Close();
};

UCLASS()
class MAKMAWORLD_API AMakmaHUD : public AHUD
{
    GENERATED_BODY()
public:
    virtual void DrawHUD() override;
    void OpenConversation(AMakmaCitizen* Citizen);
    UPROPERTY() TObjectPtr<UMakmaConversationWidget> Conversation;
};
