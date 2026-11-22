import { execFile } from 'child_process';
import { promisify } from 'util';
import * as vscode from 'vscode';

const execAsync = promisify(execFile);

export interface CheckEnvironmentResult {
    healthy: boolean;
    conflicts: Conflict[];
    packages_count: number;
}

export interface CheckPackageResult {
    safe: boolean;
    package: {
        name: string;
        version: string;
    };
    conflicts: Conflict[];
    suggestions: string[];
    confidence: number;
    caveats: string[];
}

export interface GetStableVersionResult {
    package: string;
    version: string;
    filtered: boolean;
}

export interface Conflict {
    dependency: string;
    required: string;
    installed: string;
    required_by: string;
    severity: string;
}

export class PyConflictClient {
    private pythonPath: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('pyconflict');
        this.pythonPath = config.get<string>('pythonPath', 'python');
    }

    async checkEnvironment(): Promise<CheckEnvironmentResult> {
        const result = await this.runCommand(['check-env', '--json']);
        return JSON.parse(result.stdout);
    }

    async checkPackage(packageSpec: string): Promise<CheckPackageResult> {
        // Parse package spec (e.g., "django==3.2" or "django")
        const parts = packageSpec.split('==');
        const packageName = parts[0];
        const version = parts[1];

        const args = ['check-add', packageName];
        if (version) {
            args.push('--version', version);
        }
        args.push('--json');
        const result = await this.runCommand(args);
        return JSON.parse(result.stdout);
    }

    async getStableVersion(
        packageName: string,
        pythonVersion?: string
    ): Promise<GetStableVersionResult> {
        const args = ['stable', packageName, '--json'];
        if (pythonVersion) {
            args.push('--python-version', pythonVersion);
        }
        const result = await this.runCommand(args);
        return JSON.parse(result.stdout);
    }

    private async runCommand(args: string[]): Promise<{
        stdout: string;
        stderr: string;
    }> {
        try {
            const result = await execAsync(
                this.pythonPath,
                ['-m', 'pyconflict', ...args],
                {
                timeout: 30000,
                maxBuffer: 1024 * 1024,
                encoding: 'utf8',
                }
            );
            return { stdout: String(result.stdout), stderr: String(result.stderr) };
        } catch (error: unknown) {
            // PyConflict returns non-zero exit codes for conflicts
            // We still want to parse the JSON output
            if (typeof error === 'object' && error !== null && 'stdout' in error) {
                const commandError = error as {
                    stdout?: string;
                    stderr?: string;
                    message?: string;
                };
                if (commandError.stdout) {
                    return {
                        stdout: commandError.stdout,
                        stderr: commandError.stderr || '',
                    };
                }
                throw new Error(
                    `PyConflict command failed: ${commandError.message || 'unknown error'}\n${commandError.stderr || ''}`
                );
            }
            throw error;
        }
    }
}
