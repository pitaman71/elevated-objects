import { Node as SchemaNode } from './schema';

interface Scope<TokenType> {
    open?: TokenType;
    between?: TokenType;
    close?: TokenType;
}

interface Stream<TokenType, ScopeType extends Scope<TokenType>> {
    begin(kind: ScopeType, name?: string): void;
    tokens(...tokens: TokenType[]): void;
    ws(): void;
    end(kind: ScopeType, name?: string): void;
}

export class ToString<TokenType, ScopeType extends Scope<TokenType>> {
    _result: string = "";
    _stack: { scope: ScopeType, count:number } [] = [];

    _itemStart() {
        const top = this.top();
        if(top && top.count > 0 && top.scope.between) {
            this._result += this.top()?.scope.between;
            this.ws();
        }
    }
    _itemEnd() {
        const top = this.top();
        if(top) ++top.count;
    }

    top() { return this._stack.length === 0 ? undefined : this._stack[this._stack.length - 1]; }
    begin(kind: ScopeType, name?: string): void {
        this._itemStart();
        if(kind.open) this._result += kind.open;
        this._stack.push({ scope: kind, count: 0 });
    }
    tokens(...tokens: TokenType[]): void {
        tokens.forEach(token => {
            this._itemStart();
            this._result += token;
            this._itemEnd();
        });
    }
    ws(): void {
        this._result += ' ';
    }
    end(kind: ScopeType, name?: string): void {
        if(kind.close) this._result += kind.close;
        this._stack.pop();
        this._itemEnd();
    }
}

const Parens: Scope<string> = { open: '(', close: ')' };
const Brackets: Scope<string> = { open:'[', close: ']' };
const Braces: Scope<string> = { open:'{', close: '}' };
const Commas: Scope<string> = { between: ',' };
const Semicolons: Scope<string> = { between: ';' };
const Spaces: Scope<string> = { between: ' ' };
const Adjacent: Scope<string> = { };

type TypescriptScopes = typeof Parens | typeof Brackets | typeof Braces | typeof Commas | typeof Semicolons | typeof Spaces | typeof Adjacent;

class Generator {
    _stream: Stream<string, TypescriptScopes>;
    constructor(stream: Stream<string, TypescriptScopes>) {
        this._stream = stream;
    }

    typeLiteral(decl: SchemaNode<string>) {
        if(typeof decl === "string") { 
            this._stream.tokens(decl as any);
        } else if(Array.isArray(decl)) {            
            this.typeLiteral(decl[0]);
            this._stream.begin(Brackets);
            this._stream.end(Brackets);
        } else {
            this._stream.begin(Braces);
            Object.entries(decl).forEach(([key,value]) => {
                this._stream.begin(Adjacent);
                this._stream.tokens(key, ':');
                this._stream.ws();
                this.typeLiteral(value as SchemaNode<string>);
                this._stream.tokens(';');
                this._stream.ws();
                this._stream.end(Adjacent);
            });
            this._stream.end(Braces);
        }
    }
}

export function generate(output: Generator['_stream'], ...decls: {
    schemaNode: SchemaNode<any>
}[]) {
    const generator = new Generator(output);
    decls.forEach(decl => {
        if(decl.schemaNode) {
            generator.typeLiteral(decl.schemaNode);
        }
    })
}
