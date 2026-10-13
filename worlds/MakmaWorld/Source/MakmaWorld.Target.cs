using UnrealBuildTool;
using System.Collections.Generic;
public class MakmaWorldTarget : TargetRules
{
    public MakmaWorldTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("MakmaWorld");
    }
}
