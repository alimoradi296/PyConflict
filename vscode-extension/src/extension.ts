import * as vscode from 'vscode';
import { PyConflictClient } from './pyconflictClient';
import { StatusBarManager } from './statusBar';

let client: PyConflictClient;
let statusBarManager: StatusBarManager;

export function activate(context: vscode.ExtensionContext) {
    console.log('PyConflict extension is now active');

    // Initialize client and status bar
    client = new PyConflictClient();
    statusBarManager = new StatusBarManager();

    // Register commands
    const checkEnvCommand = vscode.commands.registerCommand(
        'pyconflict.checkEnvironment',
        async () => {
            await checkEnvironment();
        }
    );

    const checkPackageCommand = vscode.commands.registerCommand(
        'pyconflict.checkPackage',
        async () => {
            const packageName = await vscode.window.showInputBox({
                prompt: 'Enter package name to check',
                placeHolder: 'e.g., django or django==3.2',
            });

            if (packageName) {
                await checkPackage(packageName);
            }
        }
    );

    const getStableVersionCommand = vscode.commands.registerCommand(
        'pyconflict.getStableVersion',
        async () => {
            const packageName = await vscode.window.showInputBox({
                prompt: 'Enter package name',
                placeHolder: 'e.g., pandas',
            });

            if (packageName) {
                await getStableVersion(packageName);
            }
        }
    );

    // Watch for file changes
    const fileWatcher = vscode.workspace.onDidSaveTextDocument(async (document) => {
        const config = vscode.workspace.getConfiguration('pyconflict');
        const autoCheck = config.get<boolean>('autoCheck', true);
        const enabled = config.get<boolean>('enabled', true);

        if (!enabled || !autoCheck) {
            return;
        }

        const fileName = document.fileName;
        if (
            fileName.endsWith('requirements.txt') ||
            fileName.endsWith('pyproject.toml') ||
            fileName.endsWith('setup.py')
        ) {
            await checkEnvironment();
        }
    });

    // Initial check
    checkEnvironment();

    // Add subscriptions
    context.subscriptions.push(
        checkEnvCommand,
        checkPackageCommand,
        getStableVersionCommand,
        fileWatcher,
        statusBarManager
    );
}

async function checkEnvironment(): Promise<void> {
    const config = vscode.workspace.getConfiguration('pyconflict');
    const enabled = config.get<boolean>('enabled', true);

    if (!enabled) {
        return;
    }

    statusBarManager.setLoading();

    try {
        const result = await client.checkEnvironment();

        if (result.healthy) {
            statusBarManager.setHealthy(0);
            vscode.window.showInformationMessage('No dependency conflicts detected');
        } else {
            const conflictCount = result.conflicts.length;
            statusBarManager.setConflicts(conflictCount);

            const message = `${conflictCount} dependency conflict${
                conflictCount > 1 ? 's' : ''
            } detected`;
            const action = await vscode.window.showWarningMessage(
                message,
                'Show Details'
            );

            if (action === 'Show Details') {
                showConflictDetails(result.conflicts);
            }
        }
    } catch (error) {
        statusBarManager.setError();
        const errorMessage =
            error instanceof Error ? error.message : 'Unknown error';
        vscode.window.showErrorMessage(`PyConflict error: ${errorMessage}`);
    }
}

async function checkPackage(packageSpec: string): Promise<void> {
    try {
        const result = await client.checkPackage(packageSpec);

        if (result.safe) {
            vscode.window.showInformationMessage(
                `✓ Safe to add ${result.package.name}==${result.package.version}`
            );
        } else {
            const conflictCount = result.conflicts.length;
            const message = `✗ Cannot add ${packageSpec}: ${conflictCount} conflict${
                conflictCount > 1 ? 's' : ''
            } detected`;

            const action = await vscode.window.showWarningMessage(
                message,
                'Show Details'
            );

            if (action === 'Show Details') {
                showConflictDetails(result.conflicts);
            }
        }
    } catch (error) {
        const errorMessage =
            error instanceof Error ? error.message : 'Unknown error';
        vscode.window.showErrorMessage(`PyConflict error: ${errorMessage}`);
    }
}

async function getStableVersion(packageName: string): Promise<void> {
    try {
        const result = await client.getStableVersion(packageName);
        vscode.window.showInformationMessage(
            `Latest stable version of ${result.package}: ${result.version}`
        );
    } catch (error) {
        const errorMessage =
            error instanceof Error ? error.message : 'Unknown error';
        vscode.window.showErrorMessage(`PyConflict error: ${errorMessage}`);
    }
}

function showConflictDetails(conflicts: any[]): void {
    const outputChannel = vscode.window.createOutputChannel('PyConflict');
    outputChannel.clear();
    outputChannel.appendLine('PyConflict - Dependency Conflicts');
    outputChannel.appendLine('='.repeat(50));
    outputChannel.appendLine('');

    conflicts.forEach((conflict, index) => {
        outputChannel.appendLine(`Conflict ${index + 1}:`);
        outputChannel.appendLine(`  Package: ${conflict.dependency}`);
        outputChannel.appendLine(`  Required: ${conflict.required}`);
        outputChannel.appendLine(`  Installed: ${conflict.installed}`);
        outputChannel.appendLine(`  Required by: ${conflict.required_by}`);
        outputChannel.appendLine('');
    });

    outputChannel.show();
}

export function deactivate() {
    console.log('PyConflict extension deactivated');
}
