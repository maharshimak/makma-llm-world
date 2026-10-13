# Architecture and implemented scope

Vinext/React operator console -> loopback FastAPI -> SQLite agent/job/memory/research kernel -> model router and constrained Docker retrieval experiments; versioned world bridge -> optional Unreal C++ campus.

Persistent agents/messages/memory, scheduler/token budgets, hypothesis-review-experiment cycles, retrieval benchmark and knowledge graph, model health/structured output, Docker isolation, snapshots/conversations and Unreal world integration.

## Modules inspected

- `worlds/MakmaWorld/Source/MakmaWorld.Target.cs`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorldEditor.Target.cs`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaCitizen.cpp`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaCitizen.h`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaGameMode.cpp`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaGameMode.h`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaHUD.cpp`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaHUD.h`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaPlayer.cpp`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaPlayer.h`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaWorld.Build.cs`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/MakmaWorld.cpp`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/WorldBridge.cpp`: source/module definitions inspected.
- `worlds/MakmaWorld/Source/MakmaWorld/WorldBridge.h`: source/module definitions inspected.
- `worlds/MakmaWorld/Scripts/build.ps1`: source/module definitions inspected.
- `worlds/MakmaWorld/Scripts/create_campus.py`: mesh, label.
- `worlds/MakmaWorld/Scripts/play.ps1`: source/module definitions inspected.
- `tests/conftest.py`: settings, store.
- `tests/test_api.py`: OfflineSandbox, test_operator_api_controls_and_persistence, health, stop_all.
- `tests/test_benchmark.py`: test_known_ranking_metrics, test_paired_bootstrap_is_reproducible, test_no_results_never_pass_validation, test_generated_code_policy, test_sandbox_command_has_no_host_mounts_and_is_constrained.
- `tests/test_kernel.py`: test_forbidden_action_batch_cannot_write_memory, test_claim_does_not_become_experimental_evidence.
- `tests/test_memory.py`: test_seed_is_idempotent_and_persistent, test_private_memory_never_crosses_owner_boundary, test_sql_injection_and_unknown_owner_do_not_retrieve_private_memories, test_context_only_contains_addressed_messages, test_read_receipts_require_correct_recipient, test_reflection_retains_sources, test_concurrent_job_claim_is_exactly_once, test_events_immutable, test_project_scoped_claim_does_not_consume_other_work.
- `tests/test_providers.py`: test_repair_once_then_safe_failure, test_repair_recovers_and_accounts_both_requests, test_extra_result_fields_rejected, test_ollama_contract, test_compatible_provider_preserves_v1_path, test_remote_model_requires_explicit_opt_in, handler, handler.
- `tests/test_research.py`: Offline, RankingDouble, test_pipeline_uses_model_then_stops_at_unavailable_sandbox, test_paused_project_does_not_claim_queued_job, test_handoff_preserves_operator_pause, test_mock_rankings_cannot_supply_numeric_metrics, health, run, run.
- `tests/test_scheduler.py`: ResearchStub, Lab, test_paused_scheduler_does_not_call_model, test_budget_prevents_inference, test_crash_recovery_does_not_replay_side_effects, stop_all.
- `tests/test_schema_regression.py`: test_schema_simplification_preserves_title_property.
- `tests/test_world.py`: world, test_world_identities_and_state_survive_restart, test_clock_pause_and_speed, test_player_position_is_owned_by_active_bridge, test_object_reservation_exclusive, test_action_ack_requires_lease_identity_and_proximity, test_connected_engine_owns_low_level_movement, test_thirty_minutes_produces_real_routine_interactions, test_economy_conserves_simulation_currency, test_player_dialogue_cannot_see_other_agents_memory.
- `scripts/build-sandbox.ps1`: source/module definitions inspected.
- `scripts/demo-research.py`: main.
- `scripts/setup.ps1`: source/module definitions inspected.
- `scripts/start.ps1`: source/module definitions inspected.
- `makma-llm-layer/install-ministral-8b.ps1`: source/module definitions inspected.
- `makma-llm-layer/setup-llm.ps1`: source/module definitions inspected.
- `makma-llm-layer/test-qwen.ps1`: source/module definitions inspected.
- `makma/api.py`: AgentCreate, TaskCreate, AccessSettings, create_app, lifespan, local_boundary, missing, invalid, denied, health, metrics, agents, create_agent, agent, memory.
- `makma/benchmark.py`: Benchmark, digest, retrieval_metrics, paired_bootstrap, validation_gate, __init__, compare.
- `makma/config.py`: Settings.
- `makma/kernel.py`: Kernel, seed, __init__, context, think, reflect, usage.
- `makma/knowledge.py`: Literature, link, __init__, search, query.
- `makma/providers.py`: ProviderUnavailable, InvalidModelOutput, ModelSpec, Completion, ModelProvider, OllamaProvider, OpenAICompatibleProvider, FutureVLLMProvider, MockProvider, ModelRouter, check_endpoint, grammar_schema, make_provider, health, complete, __init__, health, complete, close, __init__, health, complete.
- `makma/research.py`: Research, __init__, create, start, enqueue, check_budget, structured, step, current_hypothesis, handoff, failure, next_generation_or_report, learn_skill.
- `makma/sandbox.py`: SandboxUnavailable, SandboxFailure, DockerSandbox, validate_code, __init__, _command, health, command, run, stop_all, read_bounded, execute.
- `makma/scheduler.py`: Scheduler, __init__, start, loop, execute, stop, close.
- `makma/schemas.py`: Schema, Role, Personality, Belief, Agent, MemoryWrite, Action, Cognition, HypothesisDraft, Review, CodeDraft, ProjectCreate, MessageCreate, uid, now.
- `makma/store.py`: Store, __init__, connect, event, events, save_agent, agent, agents, remember, memories, send, inbox, mark_read.
- `makma/__init__.py`: source/module definitions inspected.
- `makma/world/api.py`: Embodiment, world_routes, snapshot, citizen, clock, heartbeat, event, embodiment, conversation, conversation_record, save_snapshot, stream.
- `makma/world/contracts.py`: Vector3, WorldActionV1, WorldEventV1, WorldControlV1, ConversationInputV1, ConversationReplyV1, BridgeHeartbeatV1.
- `makma/world/simulation.py`: World, distance, __init__, seed, state, save, snapshot, public_agent, start, loop, close, control, heartbeat.
- `makma/world/__init__.py`: source/module definitions inspected.
- `infrastructure/docker/harness.py`: source/module definitions inspected.
- `apps/web/next-env.d.ts`: source/module definitions inspected.
- `apps/web/next.config.ts`: source/module definitions inspected.
- `apps/web/vite.config.ts`: source/module definitions inspected.
- `apps/web/lib/api.ts`: api.
- `apps/web/lib/utils.ts`: cn.
- `apps/web/lib/webmcp.ts`: registerTools, context.
- `apps/web/hooks/use-mobile.ts`: useIsMobile, onChange.
- `apps/web/components/research-ui.tsx`: Badge, Empty, Json, ProjectCard, ProjectDialog, AgentSheet, EvidenceSheet.
- `apps/web/components/world-panel.tsx`: WorldPanel, refresh, control, save.
- `apps/web/components/ui/accordion.tsx`: Accordion, AccordionItem, AccordionTrigger, AccordionContent.
- `apps/web/components/ui/alert-dialog.tsx`: AlertDialog, AlertDialogTrigger, AlertDialogPortal, AlertDialogOverlay, AlertDialogContent, AlertDialogHeader, AlertDialogFooter, AlertDialogMedia, AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel.
- `apps/web/components/ui/alert.tsx`: Alert, AlertTitle, AlertDescription, AlertAction.
- `apps/web/components/ui/aspect-ratio.tsx`: AspectRatio.
- `apps/web/components/ui/attachment.tsx`: Attachment, AttachmentMedia, AttachmentContent, AttachmentTitle, AttachmentDescription, AttachmentActions, AttachmentAction, AttachmentTrigger, AttachmentGroup.
- `apps/web/components/ui/avatar.tsx`: Avatar, AvatarImage, AvatarFallback, AvatarBadge, AvatarGroup, AvatarGroupCount.
- `apps/web/components/ui/badge.tsx`: Badge.
- `apps/web/components/ui/breadcrumb.tsx`: Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbPage, BreadcrumbSeparator, BreadcrumbEllipsis.
- `apps/web/components/ui/bubble.tsx`: BubbleGroup, Bubble, BubbleContent, BubbleReactions.
- `apps/web/components/ui/button-group.tsx`: ButtonGroup, ButtonGroupText, ButtonGroupSeparator.
- `apps/web/components/ui/button.tsx`: Button.
- `apps/web/components/ui/calendar.tsx`: Calendar, CalendarDayButton.
- `apps/web/components/ui/card.tsx`: Card, CardHeader, CardTitle, CardDescription, CardAction, CardContent, CardFooter.
- `apps/web/components/ui/carousel.tsx`: useCarousel, Carousel, CarouselContent, CarouselItem, CarouselPrevious, CarouselNext.
- `apps/web/components/ui/chart.tsx`: useChart, ChartContainer, ChartStyle, ChartTooltipContent, ChartLegendContent, getPayloadConfigFromPayload.
- `apps/web/components/ui/checkbox.tsx`: Checkbox.
- `apps/web/components/ui/collapsible.tsx`: Collapsible, CollapsibleTrigger, CollapsibleContent.
- `apps/web/components/ui/combobox.tsx`: ComboboxValue, ComboboxTrigger, ComboboxClear, ComboboxInput, ComboboxContent, ComboboxList, ComboboxItem, ComboboxGroup, ComboboxLabel, ComboboxCollection, ComboboxEmpty, ComboboxSeparator.
- `apps/web/components/ui/command.tsx`: Command, CommandDialog, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandSeparator, CommandItem, CommandShortcut.
- `apps/web/components/ui/context-menu.tsx`: ContextMenu, ContextMenuPortal, ContextMenuTrigger, ContextMenuContent, ContextMenuGroup, ContextMenuLabel, ContextMenuItem, ContextMenuSub, ContextMenuSubTrigger, ContextMenuSubContent, ContextMenuCheckboxItem, ContextMenuRadioGroup.
- `apps/web/components/ui/dialog.tsx`: Dialog, DialogTrigger, DialogPortal, DialogClose, DialogOverlay, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription.
- `apps/web/components/ui/direction.tsx`: source/module definitions inspected.
- `apps/web/components/ui/drawer.tsx`: useDrawer, Drawer, DrawerTrigger, DrawerPortal, DrawerClose, DrawerOverlay, DrawerSwipeHandle, DrawerContent, DrawerHeader, DrawerFooter, DrawerTitle, DrawerDescription.
- `apps/web/components/ui/dropdown-menu.tsx`: DropdownMenu, DropdownMenuPortal, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuGroup, DropdownMenuLabel, DropdownMenuItem, DropdownMenuSub, DropdownMenuSubTrigger, DropdownMenuSubContent, DropdownMenuCheckboxItem, DropdownMenuRadioGroup.
- `apps/web/components/ui/empty.tsx`: Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription, EmptyContent.
- `apps/web/components/ui/field.tsx`: FieldSet, FieldLegend, FieldGroup, Field, FieldContent, FieldLabel, FieldTitle, FieldDescription, FieldSeparator, FieldError.
- `apps/web/components/ui/hover-card.tsx`: HoverCard, HoverCardTrigger, HoverCardContent.
- `apps/web/components/ui/input-group.tsx`: InputGroup, InputGroupAddon, InputGroupButton, InputGroupText, InputGroupInput, InputGroupTextarea.
- `apps/web/components/ui/input-otp.tsx`: InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator.
- `apps/web/components/ui/input.tsx`: Input.
- `apps/web/components/ui/item.tsx`: ItemGroup, ItemSeparator, Item, ItemMedia, ItemContent, ItemTitle, ItemDescription, ItemActions, ItemHeader, ItemFooter.
- `apps/web/components/ui/kbd.tsx`: Kbd, KbdGroup.
- `apps/web/components/ui/label.tsx`: Label.
- `apps/web/components/ui/marker.tsx`: Marker, MarkerIcon, MarkerContent.
- `apps/web/components/ui/menubar.tsx`: Menubar, MenubarMenu, MenubarGroup, MenubarPortal, MenubarTrigger, MenubarContent, MenubarItem, MenubarCheckboxItem, MenubarRadioGroup, MenubarRadioItem, MenubarLabel, MenubarSeparator.
- `apps/web/components/ui/message-scroller.tsx`: MessageScrollerProvider, MessageScroller, MessageScrollerViewport, MessageScrollerContent, MessageScrollerItem, MessageScrollerButton.
- `apps/web/components/ui/message.tsx`: MessageGroup, Message, MessageAvatar, MessageContent, MessageHeader, MessageFooter.
- `apps/web/components/ui/native-select.tsx`: NativeSelect, NativeSelectOption, NativeSelectOptGroup.
- `apps/web/components/ui/navigation-menu.tsx`: NavigationMenu, NavigationMenuList, NavigationMenuItem, NavigationMenuTrigger, NavigationMenuContent, NavigationMenuPositioner, NavigationMenuLink, NavigationMenuIndicator.
- `apps/web/components/ui/pagination.tsx`: Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationPrevious, PaginationNext, PaginationEllipsis.
- `apps/web/components/ui/popover.tsx`: Popover, PopoverTrigger, PopoverContent, PopoverHeader, PopoverTitle, PopoverDescription.
- `apps/web/components/ui/progress.tsx`: Progress, ProgressTrack, ProgressIndicator, ProgressLabel, ProgressValue.
- `apps/web/components/ui/radio-group.tsx`: RadioGroup, RadioGroupItem.
- `apps/web/components/ui/resizable.tsx`: ResizablePanelGroup, ResizablePanel, ResizableHandle.
- `apps/web/components/ui/scroll-area.tsx`: ScrollArea, ScrollBar.
- `apps/web/components/ui/select.tsx`: SelectGroup, SelectValue, SelectTrigger, SelectContent, SelectLabel, SelectItem, SelectSeparator, SelectScrollUpButton, SelectScrollDownButton.
- `apps/web/components/ui/separator.tsx`: Separator.
- `apps/web/components/ui/sheet.tsx`: Sheet, SheetTrigger, SheetClose, SheetPortal, SheetOverlay, SheetContent, SheetHeader, SheetFooter, SheetTitle, SheetDescription.
- `apps/web/components/ui/sidebar.tsx`: useSidebar, SidebarProvider, handleKeyDown, Sidebar, SidebarTrigger, SidebarRail, SidebarInset, SidebarInput, SidebarHeader, SidebarFooter, SidebarSeparator, SidebarContent.
- `apps/web/components/ui/skeleton.tsx`: Skeleton.
- `apps/web/components/ui/slider.tsx`: Slider.
- `apps/web/components/ui/spinner.tsx`: Spinner.
- `apps/web/components/ui/switch.tsx`: Switch.
- `apps/web/components/ui/table.tsx`: Table, TableHeader, TableBody, TableFooter, TableRow, TableHead, TableCell, TableCaption.
- `apps/web/components/ui/tabs.tsx`: Tabs, TabsList, TabsTrigger, TabsContent.
- `apps/web/components/ui/textarea.tsx`: Textarea.
- `apps/web/components/ui/toast.tsx`: ToastProvider, ToastPortal, ToastViewport, Toast, ToastContent, ToastTitle, ToastDescription, ToastAction, ToastClose, ToastIcon, ToastList, Toaster.
- `apps/web/components/ui/toggle-group.tsx`: ToggleGroup, ToggleGroupItem.
- `apps/web/components/ui/toggle.tsx`: Toggle.
- `apps/web/components/ui/tooltip.tsx`: TooltipProvider, Tooltip, TooltipTrigger, TooltipContent.
- `apps/web/app/layout.tsx`: RootLayout.
- `apps/web/app/page.tsx`: Home, act, inspect.
- `apps/web/app/api/[...path]/route.ts`: proxy.

## Request routes

| Source | Method | Path | Handler |
|---|---|---|---|
| `makma/api.py` | get | `/health` | `health` |
| `makma/api.py` | get | `/metrics` | `metrics` |
| `makma/api.py` | get | `/agents` | `agents` |
| `makma/api.py` | post | `/agents` | `create_agent` |
| `makma/api.py` | get | `/agents/{aid}` | `agent` |
| `makma/api.py` | get | `/agents/{aid}/memory` | `memory` |
| `makma/api.py` | get | `/agents/{aid}/beliefs` | `beliefs` |
| `makma/api.py` | get | `/agents/{aid}/goals` | `goals` |
| `makma/api.py` | get | `/agents/{aid}/messages` | `messages` |
| `makma/api.py` | get | `/agents/{aid}/traces` | `traces` |
| `makma/api.py` | post | `/agents/{aid}/message` | `message` |
| `makma/api.py` | post | `/agents/{aid}/task` | `task` |
| `makma/api.py` | post | `/agents/{aid}/reflect` | `reflect` |
| `makma/api.py` | post | `/research/projects` | `create_project` |
| `makma/api.py` | get | `/research/projects` | `projects` |
| `makma/api.py` | get | `/research/projects/{pid}` | `project` |
| `makma/api.py` | post | `/research/projects/{pid}/start` | `start_project` |
| `makma/api.py` | post | `/research/projects/{pid}/pause` | `pause_project` |
| `makma/api.py` | get | `/research/projects/{pid}/report` | `report` |
| `makma/api.py` | get | `/hypotheses` | `hypotheses` |
| `makma/api.py` | get | `/experiments` | `experiments` |
| `makma/api.py` | get | `/experiments/{eid}` | `experiment` |
| `makma/api.py` | get | `/discoveries` | `discoveries` |
| `makma/api.py` | get | `/knowledge/search` | `knowledge` |
| `makma/api.py` | get | `/knowledge/graph` | `graph` |
| `makma/api.py` | get | `/papers` | `papers` |
| `makma/api.py` | get | `/skills` | `skills` |
| `makma/api.py` | get | `/failures` | `failures` |
| `makma/api.py` | get | `/models` | `models` |
| `makma/api.py` | get | `/jobs` | `jobs` |
| `makma/api.py` | post | `/jobs/{jid}/retry` | `retry` |
| `makma/api.py` | post | `/world/pause` | `pause` |
| `makma/api.py` | post | `/world/resume` | `resume` |
| `makma/api.py` | post | `/world/stop` | `stop` |
| `makma/api.py` | post | `/world/budget/reset` | `budget_reset` |
| `makma/api.py` | post | `/settings` | `update_settings` |
| `makma/api.py` | get | `/events` | `events` |
| `makma/api.py` | get | `/events/stream` | `stream` |
| `makma/world/api.py` | get | `/snapshot` | `snapshot` |
| `makma/world/api.py` | get | `/citizens/{aid}` | `citizen` |
| `makma/world/api.py` | post | `/clock` | `clock` |
| `makma/world/api.py` | post | `/bridge/heartbeat` | `heartbeat` |
| `makma/world/api.py` | post | `/bridge/events` | `event` |
| `makma/world/api.py` | post | `/embodiment` | `embodiment` |
| `makma/world/api.py` | post | `/conversation` | `conversation` |
| `makma/world/api.py` | get | `/conversations/{cid}` | `conversation_record` |
| `makma/world/api.py` | post | `/snapshot/save` | `save_snapshot` |
| `makma/world/api.py` | websocket | `/stream` | `stream` |

Static parsing found the modules/handlers above without importing/executing them. Fixtures, enums and abstract declarations are not proof that every flow is complete. See TECHNICAL_ISSUES.md for incomplete adapters and inconsistent pipeline contracts.
