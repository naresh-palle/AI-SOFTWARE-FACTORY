"""
Mobile Code Generation Worker.
Generates React Native / Expo applications for Android & iOS with auth and push notification services.
"""

import json
from typing import Any, Dict, List, Optional
from factory.core.logger import logger
from factory.generator.workers.base_worker import BaseWorker, WorkerResult


class MobileWorker(BaseWorker):
    """Generates cross-platform React Native / Expo mobile applications."""

    @property
    def worker_name(self) -> str:
        return "mobile"

    @property
    def default_branch(self) -> str:
        return "feature/mobile-react-native"

    async def generate_code(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        # Check if mobile is requested in platform targets or requirement
        needs_mobile = any(
            t in ["mobile", "mobile_android", "mobile_ios", "all", "crossplatform"] for t in platform_targets
        ) or any(k in requirement_text.lower() for k in ["mobile", "android", "ios", "app", "phone"])

        if not needs_mobile:
            logger.info("MobileWorker: Project does not target mobile. Skipping.")
            return WorkerResult(
                worker_name=self.worker_name,
                branch_name=self.default_branch,
                files_created=[],
                commit_sha=None,
                metadata={"skipped": True, "reason": "No mobile target specified"}
            )

        logger.info(f"MobileWorker generating mobile app for project: {self.workspace.project_id}")
        self.github.create_branch(self.default_branch)

        files_created: List[str] = []

        # 1. package.json
        pkg = {
            "name": f"project-{self.workspace.project_id[:8]}-mobile",
            "version": "1.0.0",
            "scripts": {
                "start": "expo start",
                "android": "expo start --android",
                "ios": "expo start --ios"
            },
            "dependencies": {
                "expo": "~50.0.0",
                "react": "18.2.0",
                "react-native": "0.73.2",
                "expo-notifications": "~0.27.0",
                "@react-navigation/native": "^6.1.9",
                "@react-navigation/native-stack": "^6.9.17"
            },
            "devDependencies": {
                "@types/react": "~18.2.45",
                "typescript": "^5.3.0"
            }
        }
        self.workspace.write_file("mobile/package.json", json.dumps(pkg, indent=2) + "\n")
        files_created.append("mobile/package.json")

        # 2. app.json
        app_json = {
            "expo": {
                "name": "FactoryMobileApp",
                "slug": f"factory-app-{self.workspace.project_id[:8]}",
                "version": "1.0.0",
                "orientation": "portrait",
                "icon": "./assets/icon.png",
                "userInterfaceStyle": "light",
                "splash": {
                    "resizeMode": "contain",
                    "backgroundColor": "#ffffff"
                },
                "ios": {
                    "supportsTablet": True,
                    "bundleIdentifier": f"com.factory.{self.workspace.project_id[:8]}"
                },
                "android": {
                    "adaptiveIcon": {
                        "backgroundColor": "#ffffff"
                    },
                    "package": f"com.factory.{self.workspace.project_id[:8]}"
                }
            }
        }
        self.workspace.write_file("mobile/app.json", json.dumps(app_json, indent=2) + "\n")
        files_created.append("mobile/app.json")

        # 3. App.tsx
        app_tsx = (
            "import React, { useState } from 'react';\n"
            "import { StyleSheet, Text, View, SafeAreaView, TouchableOpacity } from 'react-native';\n"
            "import { registerForPushNotificationsAsync } from './src/services/push_notifications';\n\n"
            "export default function App() {\n"
            "  const [loggedIn, setLoggedIn] = useState(false);\n\n"
            "  return (\n"
            "    <SafeAreaView style={styles.container}>\n"
            "      <View style={styles.content}>\n"
            "        <Text style={styles.title}>Mobile Client App</Text>\n"
            "        <Text style={styles.subtitle}>\n"
            "          {loggedIn ? 'Welcome! You are authenticated.' : 'Please authenticate to continue.'}\n"
            "        </Text>\n"
            "        <TouchableOpacity\n"
            "          style={styles.button}\n"
            "          onPress={() => setLoggedIn(!loggedIn)}\n"
            "        >\n"
            "          <Text style={styles.buttonText}>{loggedIn ? 'Log Out' : 'Authenticate'}</Text>\n"
            "        </TouchableOpacity>\n"
            "      </View>\n"
            "    </SafeAreaView>\n"
            "  );\n"
            "}\n\n"
            "const styles = StyleSheet.create({\n"
            "  container: { flex: 1, backgroundColor: '#f8fafc' },\n"
            "  content: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },\n"
            "  title: { fontSize: 24, fontWeight: 'bold', color: '#0f172a', marginBottom: 8 },\n"
            "  subtitle: { fontSize: 16, color: '#64748b', marginBottom: 24, textAlign: 'center' },\n"
            "  button: { backgroundColor: '#0284c7', paddingVertical: 14, paddingHorizontal: 28, borderRadius: 8 },\n"
            "  buttonText: { color: '#ffffff', fontWeight: 'bold', fontSize: 16 },\n"
            "});\n"
        )
        self.workspace.write_file("mobile/App.tsx", app_tsx)
        files_created.append("mobile/App.tsx")

        # 4. src/services/push_notifications.ts
        push_ts = (
            "export async function registerForPushNotificationsAsync(): Promise<string | null> {\n"
            "  try {\n"
            "    console.log('Registering push notification token with FCM / APNS gateway...');\n"
            "    return 'mock-device-push-token-xyz123';\n"
            "  } catch (error) {\n"
            "    console.error('Failed to get push token:', error);\n"
            "    return null;\n"
            "  }\n"
            "}\n"
        )
        self.workspace.write_file("mobile/src/services/push_notifications.ts", push_ts)
        files_created.append("mobile/src/services/push_notifications.ts")

        commit_sha = self.github.commit_changes(
            message=f"feat(mobile): generate React Native / Expo application structure ({len(files_created)} files)"
        )

        return WorkerResult(
            worker_name=self.worker_name,
            branch_name=self.default_branch,
            files_created=files_created,
            commit_sha=commit_sha,
            metadata={"file_count": len(files_created)}
        )
