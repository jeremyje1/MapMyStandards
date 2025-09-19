import * as vscode from 'vscode';

class A3EGapsProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData: vscode.Event<void> = this._onDidChangeTreeData.event;

  constructor(private context: vscode.ExtensionContext) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  async getChildren(): Promise<vscode.TreeItem[]> {
    // Minimal placeholder: could fetch from /api/v1/gaps?program_id=...
    const sample = new vscode.TreeItem('Select standards to view gaps');
    sample.iconPath = new vscode.ThemeIcon('warning');
    sample.command = { command: 'a3e.openGapsWebView', title: 'Open A3E Gaps', arguments: [] };
    return [sample];
  }
}

class EvidenceCodeLensProvider implements vscode.CodeLensProvider {
  private codeLenses: vscode.CodeLens[] = [];
  private regex = /^(#+)\s+.+/gm;

  provideCodeLenses(document: vscode.TextDocument): vscode.ProviderResult<vscode.CodeLens[]> {
    this.codeLenses = [];
    const text = document.getText();
    let matches;
    while ((matches = this.regex.exec(text)) !== null) {
      const line = document.positionAt(matches.index).line;
      const range = new vscode.Range(line, 0, line, matches[0].length);
      this.codeLenses.push(new vscode.CodeLens(range, {
        title: 'Insert Evidence Snippet…',
        command: 'a3e.insertEvidenceSnippet',
        arguments: [document.uri, line]
      }));
    }
    return this.codeLenses;
  }
}

export function activate(context: vscode.ExtensionContext) {
  const provider = new A3EGapsProvider(context);
  vscode.window.registerTreeDataProvider('A3E.showGaps', provider);

  context.subscriptions.push(
    vscode.commands.registerCommand('a3e.refreshGaps', () => provider.refresh()),
    vscode.commands.registerCommand('a3e.openGapsWebView', () => openGapsWebView(context)),
    vscode.commands.registerCommand('a3e.insertEvidenceSnippet', (uri: vscode.Uri, line: number) => insertEvidenceSnippet(uri, line))
  );

  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider({ language: 'markdown' }, new EvidenceCodeLensProvider())
  );
}

async function openGapsWebView(context: vscode.ExtensionContext) {
  const panel = vscode.window.createWebviewPanel(
    'a3eGaps',
    'A3E — Gaps',
    vscode.ViewColumn.Beside,
    { enableScripts: true }
  );

  panel.webview.html = `
    <!doctype html>
    <html><head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style> body { font-family: sans-serif; padding: 12px; } .pill{padding:2px 8px;border-radius:999px;margin-right:6px} .red{background:#fee2e2} .amber{background:#fef3c7} .green{background:#dcfce7}</style>
    </head><body>
      <h2>Standards Gaps</h2>
      <p>Connect to A3E API and display Red/Amber/Green pills.</p>
      <div>
        <span class="pill red">High Risk</span>
        <span class="pill amber">Medium</span>
        <span class="pill green">Low</span>
      </div>
      <p style="margin-top:12px">Configure API base via <code>a3e.apiBase</code> setting.</p>
    </body></html>
  `;
}

async function insertEvidenceSnippet(uri: vscode.Uri, line: number) {
  const editor = await vscode.window.showTextDocument(uri);
  const snippet = new vscode.SnippetString('\n> Evidence: ${1:paste summary here}\n');
  editor.insertSnippet(snippet, new vscode.Position(line + 1, 0));
}

export function deactivate() {}
