# GROOMING REPORT: 2025-07-28

### Summary
- Issues Reviewed: 139 - Tasks Migrated: 139 - Open Issues Created: 17
- Closed Issues Created: 122

### 🏷️ Label Creation Commands (Execute these first!)
```bash
gh label create '✨ migrated' --color '0e8a16' || true
gh label create '⬆️ priority: 1' --color 'b60205' || true
gh label create '⬆️ priority: 2' --color 'd93f0b' || true
gh label create '⬆️ priority: 3' --color 'fbca04' || true
gh label create '⬆️ priority: 4' --color '009800' || true
gh label create '⬆️ priority: 5' --color '006b75' || true
gh label create '🤖 agent' --color 'ededed' || true
gh label create ' agents' --color 'ededed' || true
gh label create '🚀 ci' --color 'ededed' || true
gh label create '⚙️ config' --color 'ededed' || true
gh label create '🗄️ db' --color 'ededed' || true
gh label create '📚 docs' --color 'ededed' || true
gh label create '📄 documentation' --color 'ededed' || true
gh label create '💻 frontend' --color 'ededed' || true
gh label create '📈 infra' --color 'ededed' || true
gh label create '🏗️ infrastructure' --color 'ededed' || true
gh label create '🌐 ops' --color 'ededed' || true
gh label create '🔒 security' --color 'ededed' || true
gh label create '🖥️ server' --color 'ededed' || true
gh label create '💾 state' --color 'ededed' || true
gh label create '📞 telephony' --color 'ededed' || true
gh label create '🧪 testing' --color 'ededed' || true
gh label create ' tests' --color 'ededed' || true
gh label create '📦 tooling' --color 'ededed' || true
gh label create '🛠️ tools' --color 'ededed' || true
gh label create '🎨 ui' --color 'ededed' || true
```

### 📝 Issue Creation Commands (Execute these next!)
```bash
gh issue create --title '🏗️ Set up project directory and file structure' --body-file 'temp/issue_1.md'
gh issue create --title '⚙️ Configure .env and environment secrets' --body-file 'temp/issue_2.md'
gh issue create --title '🤖 Implement latency logger with loguru' --body-file 'temp/issue_3.md'
gh issue create --title '🤖 Add STT warm-up daemon for Whisper' --body-file 'temp/issue_4.md'
gh issue create --title '🖥️ Build minimal Vocode Flask app with Twilio webhook' --body-file 'temp/issue_5.md'
gh issue create --title '🤖 Create core conversational agent configuration' --body-file 'temp/issue_6.md'
gh issue create --title '🛠️ Set up local microphone/speaker test script' --body-file 'temp/issue_7.md'
gh issue create --title '🖥️ Handle incoming call, STT, TTS, and response' --body-file 'temp/issue_8.md'
gh issue create --title '📞 Enable and store call recordings' --body-file 'temp/issue_9.md'
gh issue create --title '📞 Implement recording status webhook' --body-file 'temp/issue_35.md'
gh issue create --title '🤖 Transcribe call audio after hangup' --body-file 'temp/issue_10.md'
gh issue create --title '🛠️ Send transcript and audio to user via email/SMS' --body-file 'temp/issue_11.md'
gh issue create --title '💾 Add Redis support for short-term state tracking' --body-file 'temp/issue_12.md'
gh issue create --title '🤖 Add OpenAI function-calling support to agent' --body-file 'temp/issue_13.md'
gh issue create --title '🛠️ Integrate simple tool: weather API' --body-file 'temp/issue_14.md'
gh issue create --title '🛠️ Build Google Calendar tool with OAuth' --body-file 'temp/issue_15.md'
gh issue create --title '💾 Store refresh tokens and OAuth metadata' --body-file 'temp/issue_16.md'
gh issue create --title '🤖 Implement fallback for tool auth failure' --body-file 'temp/issue_17.md'
gh issue create --title '🤖 Add escalation triggers based on keywords' --body-file 'temp/issue_18.md'
gh issue create --title '🤖 Summarize conversation before handoff' --body-file 'temp/issue_19.md'
gh issue create --title '📞 Forward live call to mobile number' --body-file 'temp/issue_20.md'
gh issue create --title '🛠️ Notify user of handoff via SMS/email' --body-file 'temp/issue_21.md'
gh issue create --title '💾 Persist call summaries and preferences' --body-file 'temp/issue_22.md'
gh issue create --title '💾 Add semantic memory support with ChromaDB or pgvector' --body-file 'temp/issue_23.md'
gh issue create --title '🤖 Implement Safety Oracle function' --body-file 'temp/issue_24.md'
gh issue create --title '🛠️ Red-team simulation engine' --body-file 'temp/issue_25.md'
gh issue create --title '🤖 Add self-reflection routine to agent' --body-file 'temp/issue_26.md'
gh issue create --title '🎨 Create basic dashboard to list transcripts and recordings' --body-file 'temp/issue_27.md'
gh issue create --title '🎨 Add search, playback, and call metadata view' --body-file 'temp/issue_28.md'
gh issue create --title '🎨 Add RBAC for admin access and logs' --body-file 'temp/issue_29.md'
gh issue create --title '🏗️ Introduce Celery worker & docker‑compose service' --body-file 'temp/issue_30.md'
gh issue create --title '🏗️ Add encryption libs to Docker image' --body-file 'temp/issue_31.md'
gh issue create --title '🧪 Add unit tests for StateManager and TokenStore' --body-file 'temp/issue_32.md'
gh issue create --title '🏗️ Integrate Prometheus exporter for latency metrics' --body-file 'temp/issue_33.md'
gh issue create --title '🔒 Add git-secrets pre‑commit hook' --body-file 'temp/issue_34.md'
gh issue create --title '📄 Create CONTRIBUTING.md' --body-file 'temp/issue_36.md'
gh issue create --title '📄 Add LICENSE file' --body-file 'temp/issue_37.md'
gh issue create --title '🏗️ Set up GitHub Actions CI workflow' --body-file 'temp/issue_38.md'
gh issue create --title '🔒 Set up GitHub Actions security scan' --body-file 'temp/issue_39.md'
gh issue create --title '📦 Add .pre-commit-config.yaml' --body-file 'temp/issue_40.md'
gh issue create --title ' Scaffold CoordinatorAgent skeleton' --body-file 'temp/issue_41.md'
gh issue create --title ' Implement TestCrafterPro (TC) reviewer' --body-file 'temp/issue_42.md'
gh issue create --title ' Implement SafetyOracle bot' --body-file 'temp/issue_43.md'
gh issue create --title ' Implement secondary CodeGenius logic reviewer' --body-file 'temp/issue_44.md'
gh issue create --title '🏗️ Deploy GitHub App for CoordinatorAgent automation' --body-file 'temp/issue_45.md'
gh issue create --title '🖥️ Configuration Loader' --body-file 'temp/issue_46.md'
gh issue create --title '🖥️ Persistent Encryption Key' --body-file 'temp/issue_47.md'
gh issue create --title '🖥️ Versioned API with Validation' --body-file 'temp/issue_48.md'
gh issue create --title '📦 Clean requirements' --body-file 'temp/issue_49.md'
gh issue create --title '🚀 Pre-commit in CI' --body-file 'temp/issue_50.md'
gh issue create --title '🏗️ Provision Grafana dashboard' --body-file 'temp/issue_51.md'
gh issue create --title '🏗️ Configure Prometheus alert rules' --body-file 'temp/issue_52.md'
gh issue create --title '🔒 Container image security scanning' --body-file 'temp/issue_53.md'
gh issue create --title '🧪 End-to-end call flow test' --body-file 'temp/issue_54.md'
gh issue create --title '🎨 OAuth login for dashboard' --body-file 'temp/issue_55.md'
gh issue create --title '💾 Summarization-aware memory retrieval' --body-file 'temp/issue_56.md'
gh issue create --title '🖥️ API key authentication' --body-file 'temp/issue_57.md'
gh issue create --title '🤖 Multilingual call support' --body-file 'temp/issue_58.md'
gh issue create --title '🏗️ Data retention cleanup job' --body-file 'temp/issue_59.md'
gh issue create --title '🔒 Rate limiting and abuse protection' --body-file 'temp/issue_60.md'
gh issue create --title '🖥️ Timezone-aware datetime handling' --body-file 'temp/issue_61.md'
gh issue create --title '📄 Document pre-commit hooks' --body-file 'temp/issue_62.md'
gh issue create --title '🖥️ Centralize environment configuration' --body-file 'temp/issue_63.md'
gh issue create --title '🛠️ Harden external API error handling' --body-file 'temp/issue_64.md'
gh issue create --title '🖥️ Add indexes for call history queries' --body-file 'temp/issue_65.md'
gh issue create --title '📄 Publish API and CLI reference' --body-file 'temp/issue_66.md'
gh issue create --title '🛠️ Provide unified `tel3sis` CLI' --body-file 'temp/issue_67.md'
gh issue create --title '🧪 Add integration tests for CLI and endpoints' --body-file 'temp/issue_68.md'
gh issue create --title '📦 Adopt pip-tools for dependency management' --body-file 'temp/issue_69.md'
gh issue create --title '🏗️ Optimize Docker build with multi-stage and .dockerignore' --body-file 'temp/issue_70.md'
gh issue create --title '🚀 Cache pip and Docker layers in CI' --body-file 'temp/issue_71.md'
gh issue create --title '🚀 Publish Docker image on release' --body-file 'temp/issue_72.md'
gh issue create --title '🧪 Test Docker Compose deployment' --body-file 'temp/issue_73.md'
gh issue create --title '🖥️ Complete FastAPI migration and remove Flask remnants' --body-file 'temp/issue_74.md'
gh issue create --title '⚙️ Implement centralized configuration management' --body-file 'temp/issue_75.md'
gh issue create --title '🚀 Add dependency vulnerability scanning to CI/CD' --body-file 'temp/issue_76.md'
gh issue create --title '🖥️ Implement caching for LLM and external API responses' --body-file 'temp/issue_77.md'
gh issue create --title '📄 Develop production deployment guide' --body-file 'temp/issue_78.md'
gh issue create --title '🤖 Enhance end-user voice error handling' --body-file 'temp/issue_79.md'
gh issue create --title '🧪 Create shared `vocode` mocking utility for tests' --body-file 'temp/issue_80.md'
gh issue create --title '🛠️ Expand CLI user management capabilities' --body-file 'temp/issue_81.md'
gh issue create --title '🏗️ Implement latency monitoring and optimization strategy for VUI' --body-file 'temp/issue_82.md'
gh issue create --title '🎨 Enhance dashboard with filtering, sorting, and pagination' --body-file 'temp/issue_83.md'
gh issue create --title '🎨 Develop an analytical overview dashboard' --body-file 'temp/issue_84.md'
gh issue create --title '🤖 Implement barge-in (interruption handling) in VUI' --body-file 'temp/issue_85.md'
gh issue create --title '🎨 Add actionability to the dashboard' --body-file 'temp/issue_86.md'
gh issue create --title '🎨 Implement global search for call history' --body-file 'temp/issue_87.md'
gh issue create --title '🤖 Implement Intent Recognition' --body-file 'temp/issue_88.md'
gh issue create --title '🤖 Develop Multi-Turn Dialogue State Machine' --body-file 'temp/issue_89.md'
gh issue create --title '🤖 Refactor Tools for Dynamic Invocation' --body-file 'temp/issue_90.md'
gh issue create --title '🖥️ Integrate Twilio SMS for Inbound/Outbound Messaging' --body-file 'temp/issue_91.md'
gh issue create --title '🖥️ Design Generic Web Chat API' --body-file 'temp/issue_92.md'
gh issue create --title '🤖 Implement Long-Term Memory Retrieval' --body-file 'temp/issue_93.md'
gh issue create --title '🤖 Develop Conversation Summarization Logic' --body-file 'temp/issue_94.md'
gh issue create --title '⚙️ Centralize Configuration with Pydantic' --body-file 'temp/issue_95.md'
gh issue create --title '🖥️ Instrument Application with Prometheus Metrics' --body-file 'temp/issue_96.md'
gh issue create --title '📈 Build Grafana Dashboard for Monitoring' --body-file 'temp/issue_97.md'
gh issue create --title '📈 Set Up Alertmanager for Critical Alerts' --body-file 'temp/issue_98.md'
gh issue create --title '🗄️ Document and Automate Database Backup/Restore' --body-file 'temp/issue_99.md'
gh issue create --title '🛠️ Harden Error Handling for All External APIs' --body-file 'temp/issue_100.md'
gh issue create --title '🖥️ Implement Transactional State Updates' --body-file 'temp/issue_101.md'
gh issue create --title '💻 Design and Build Admin UI Frontend' --body-file 'temp/issue_102.md'
gh issue create --title '🖥️ Create Backend API for Admin UI' --body-file 'temp/issue_103.md'
gh issue create --title '💻 Implement Conversation Log Viewer' --body-file 'temp/issue_104.md'
gh issue create --title '💻 Build Agent Configuration Interface' --body-file 'temp/issue_105.md'
gh issue create --title '🖥️ Design Secure OAuth2 Onboarding Flow' --body-file 'temp/issue_106.md'
gh issue create --title '🖥️ Generate API Documentation with OpenAPI' --body-file 'temp/issue_107.md'
gh issue create --title '📚 Write Comprehensive User Guide' --body-file 'temp/issue_108.md'
gh issue create --title '📚 Create Detailed Architecture Diagram' --body-file 'temp/issue_109.md'
gh issue create --title '📚 Write a Developer Onboarding Guide' --body-file 'temp/issue_110.md'
gh issue create --title '📚 Document Configuration Variables' --body-file 'temp/issue_111.md'
gh issue create --title '📦 Enforce production dependency separation' --body-file 'temp/issue_112.md'
gh issue create --title '🚀 Automate dependency lock updates' --body-file 'temp/issue_113.md'
gh issue create --title '🤖 Refine agent error handling' --body-file 'temp/issue_114.md'
gh issue create --title '🖥️ Remove direct os.environ usage' --body-file 'temp/issue_115.md'
gh issue create --title '🖥️ Migrate to async database driver' --body-file 'temp/issue_116.md'
gh issue create --title '🧪 Add tests for CLI and tool error cases' --body-file 'temp/issue_117.md'
gh issue create --title '🖥️ Standardize logging across modules' --body-file 'temp/issue_118.md'
gh issue create --title '📚 Publish Drift Analysis Report' --body-file 'temp/issue_119.md'
gh issue create --title '🖥️ Multi-language voice support' --body-file 'temp/issue_120.md'
gh issue create --title '🖥️ Sentiment analysis for summaries' --body-file 'temp/issue_121.md'
gh issue create --title '🖥️ Live agent status via WebSocket' --body-file 'temp/issue_122.md'
gh issue create --title '🛠️ Translation tool' --body-file 'temp/issue_123.md'
gh issue create --title '🛠️ Knowledge base FAQ tool' --body-file 'temp/issue_124.md'
gh issue create --title '🖥️ Vector store pruning' --body-file 'temp/issue_125.md'
gh issue create --title '🖥️ Conversation topic classification' --body-file 'temp/issue_126.md'
gh issue create --title '🖥️ Slack escalation' --body-file 'temp/issue_127.md'
gh issue create --title ' Custom banned phrase lists' --body-file 'temp/issue_128.md'
gh issue create --title '🖥️ Two-factor authentication' --body-file 'temp/issue_129.md'
gh issue create --title '🌐 Kubernetes deployment' --body-file 'temp/issue_130.md'
gh issue create --title '🖥️ Healthcheck endpoints' --body-file 'temp/issue_131.md'
gh issue create --title '🚀 Coverage reporting' --body-file 'temp/issue_132.md'
gh issue create --title ' Property-based call-flow tests' --body-file 'temp/issue_133.md'
gh issue create --title '📚 Admin UI guide' --body-file 'temp/issue_134.md'
gh issue create --title '📚 Contribution style guide' --body-file 'temp/issue_135.md'
gh issue create --title '🖥️ Centralized log forwarding' --body-file 'temp/issue_136.md'
gh issue create --title '💻 Admin UI dark mode' --body-file 'temp/issue_137.md'
gh issue create --title '📦 Devcontainer support' --body-file 'temp/issue_138.md'
gh issue create --title '🤖 Plugin architecture for tools' --body-file 'temp/issue_139.md'
```

### ➕ Labeling Existing Issues (After creation, fill in ISSUE_NUMBER manually)
```bash
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,🏗️ infrastructure' # Task ID: INIT-00
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,⚙️ config' # Task ID: INIT-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: INIT-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,🤖 agent' # Task ID: INIT-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,🖥️ server' # Task ID: INIT-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,🤖 agent' # Task ID: CORE-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🛠️ tools' # Task ID: CORE-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,🖥️ server' # Task ID: CORE-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📞 telephony' # Task ID: CORE-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📞 telephony' # Task ID: CORE-04A
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🤖 agent' # Task ID: CORE-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🛠️ tools' # Task ID: CORE-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,💾 state' # Task ID: MEM-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🤖 agent' # Task ID: TOOL-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🛠️ tools' # Task ID: TOOL-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🛠️ tools' # Task ID: TOOL-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,💾 state' # Task ID: TOOL-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🤖 agent' # Task ID: TOOL-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: FWD-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: FWD-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,📞 telephony' # Task ID: FWD-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🛠️ tools' # Task ID: FWD-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,💾 state' # Task ID: MEM-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,💾 state' # Task ID: MEM-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🤖 agent' # Task ID: SAFE-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,🛠️ tools' # Task ID: SAFE-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,🤖 agent' # Task ID: SAFE-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🎨 ui' # Task ID: UI-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,🎨 ui' # Task ID: UI-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,🎨 ui' # Task ID: UI-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🏗️ infrastructure' # Task ID: OPS-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🏗️ infrastructure' # Task ID: OPS-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🧪 testing' # Task ID: QA-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🏗️ infrastructure' # Task ID: MON-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🔒 security' # Task ID: SEC-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📄 documentation' # Task ID: DOC-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,📄 documentation' # Task ID: DOC-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🏗️ infrastructure' # Task ID: CI-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🔒 security' # Task ID: CI-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📦 tooling' # Task ID: DEV-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,agents' # Task ID: AGENT-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,agents' # Task ID: AGENT-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,agents' # Task ID: AGENT-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,agents' # Task ID: AGENT-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🏗️ infrastructure' # Task ID: AGENT-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: CORE-16
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: CORE-17
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: API-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📦 tooling' # Task ID: OPS-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🚀 ci' # Task ID: CI-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🏗️ infrastructure' # Task ID: MON-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🏗️ infrastructure' # Task ID: MON-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🔒 security' # Task ID: OPS-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🧪 testing' # Task ID: QA-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🎨 ui' # Task ID: UI-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,💾 state' # Task ID: MEM-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: API-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 5,🤖 agent' # Task ID: CORE-18
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🏗️ infrastructure' # Task ID: OPS-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🔒 security' # Task ID: SAFE-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🖥️ server' # Task ID: CORE-19
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,📄 documentation' # Task ID: DOC-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: ARCH-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🛠️ tools' # Task ID: ARCH-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: ARCH-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📄 documentation' # Task ID: DOC-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🛠️ tools' # Task ID: CLI-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🧪 testing' # Task ID: QA-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📦 tooling' # Task ID: DEV-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🏗️ infrastructure' # Task ID: OPS-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🚀 ci' # Task ID: CI-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🚀 ci' # Task ID: CI-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🧪 testing' # Task ID: QA-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: REF-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,⚙️ config' # Task ID: CONF-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🚀 ci' # Task ID: CI-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: PERF-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,📄 documentation' # Task ID: DOC-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🤖 agent' # Task ID: UX-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🧪 testing' # Task ID: QA-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🛠️ tools' # Task ID: CLI-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,🏗️ infrastructure' # Task ID: UIX-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🎨 ui' # Task ID: UIX-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🎨 ui' # Task ID: UIX-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: UIX-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🎨 ui' # Task ID: UIX-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🎨 ui' # Task ID: UIX-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: CORE-20
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: CORE-21
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: CORE-22
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🖥️ server' # Task ID: CORE-23
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: CORE-24
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: CORE-25
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: CORE-26
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,⚙️ config' # Task ID: PROD-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🖥️ server' # Task ID: PROD-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,📈 infra' # Task ID: PROD-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,📈 infra' # Task ID: PROD-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🗄️ db' # Task ID: PROD-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🛠️ tools' # Task ID: PROD-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: PROD-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,💻 frontend' # Task ID: UX-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🖥️ server' # Task ID: UX-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,💻 frontend' # Task ID: UX-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,💻 frontend' # Task ID: UX-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🖥️ server' # Task ID: UX-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: DOCS-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,📚 docs' # Task ID: DOCS-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📚 docs' # Task ID: DOCS-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,📚 docs' # Task ID: DOCS-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📚 docs' # Task ID: DOCS-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,📦 tooling' # Task ID: OPS-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🚀 ci' # Task ID: CI-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🤖 agent' # Task ID: CORE-27
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🖥️ server' # Task ID: CONF-03
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🖥️ server' # Task ID: ARCH-04
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🧪 testing' # Task ID: QA-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🖥️ server' # Task ID: LOG-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📚 docs' # Task ID: DOCS-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: CORE-28
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🖥️ server' # Task ID: CORE-29
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: CORE-30
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🛠️ tools' # Task ID: TOOL-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🛠️ tools' # Task ID: TOOL-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🖥️ server' # Task ID: MEM-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: MEM-06
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🖥️ server' # Task ID: FWD-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,agents' # Task ID: SAFE-05
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🖥️ server' # Task ID: SEC-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,🌐 ops' # Task ID: OPS-08
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🖥️ server' # Task ID: OPS-09
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🚀 ci' # Task ID: CI-08
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 3,tests' # Task ID: QA-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📚 docs' # Task ID: DOCS-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📚 docs' # Task ID: DOCS-08
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,🖥️ server' # Task ID: LOG-02
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 1,💻 frontend' # Task ID: UX-07
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 2,📦 tooling' # Task ID: DX-01
gh issue edit <ISSUE_NUMBER> --add-label '✨ migrated,⬆️ priority: 4,🤖 agent' # Task ID: ARCH-05
```

### ⚠️ Important Notes:
1.  **Run commands from project root:** The `gh issue create` commands use relative paths for `--body-file`. Ensure you execute these commands from the `/Users/adrian/repos/TEL3SIS/` directory.
2.  **Manual Closing for "Done" Issues:** The `gh issue create` command does not support a `--close` flag. For tasks marked as `status: done` in `tasks.yml`, you will need to manually close the corresponding GitHub issues after they are created.
3.  **Temporary Files:** This process creates temporary Markdown files in the `temp/` directory for issue bodies. These files are necessary for the `gh issue create` commands to function correctly. Do not delete them until after you have successfully created all issues.
4.  **Clean up temporary files:** After successfully migrating all issues, you can delete the `temp/` directory and its contents: `rm -rf /Users/adrian/repos/TEL3SIS/temp`
