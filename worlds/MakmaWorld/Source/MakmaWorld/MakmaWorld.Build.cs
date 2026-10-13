using UnrealBuildTool;
public class MakmaWorld : ModuleRules
{
    public MakmaWorld(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new [] {"Core","CoreUObject","Engine","InputCore","AIModule","NavigationSystem","HTTP","Json","JsonUtilities","UMG","Slate","SlateCore"});
    }
}
