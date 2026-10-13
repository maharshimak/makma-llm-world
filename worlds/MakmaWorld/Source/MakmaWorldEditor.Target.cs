using UnrealBuildTool;
using System.Collections.Generic;
public class MakmaWorldEditorTarget : TargetRules
{
    public MakmaWorldEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("MakmaWorld");
    }
}
