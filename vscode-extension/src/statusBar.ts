import * as vscode from 'vscode';

export class StatusBarManager implements vscode.Disposable {
    private statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );
        this.statusBarItem.command = 'pyconflict.checkEnvironment';

        const config = vscode.workspace.getConfiguration('pyconflict');
        const showStatusBar = config.get<boolean>('showStatusBar', true);

        if (showStatusBar) {
            this.statusBarItem.show();
        }
    }

    setLoading(): void {
        this.statusBarItem.text = '$(sync~spin) Checking dependencies...';
        this.statusBarItem.backgroundColor = undefined;
        this.statusBarItem.tooltip = 'PyConflict is checking dependencies';
    }

    setHealthy(conflictCount: number): void {
        this.statusBarItem.text = '$(check) No conflicts';
        this.statusBarItem.backgroundColor = undefined;
        this.statusBarItem.tooltip = 'All dependencies are compatible';
    }

    setConflicts(conflictCount: number): void {
        this.statusBarItem.text = `$(warning) ${conflictCount} conflict${
            conflictCount > 1 ? 's' : ''
        }`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor(
            'statusBarItem.warningBackground'
        );
        this.statusBarItem.tooltip = `${conflictCount} dependency conflict${
            conflictCount > 1 ? 's' : ''
        } detected. Click to check.`;
    }

    setError(): void {
        this.statusBarItem.text = '$(x) PyConflict error';
        this.statusBarItem.backgroundColor = new vscode.ThemeColor(
            'statusBarItem.errorBackground'
        );
        this.statusBarItem.tooltip =
            'PyConflict error. Click to check environment.';
    }

    show(): void {
        this.statusBarItem.show();
    }

    hide(): void {
        this.statusBarItem.hide();
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}
