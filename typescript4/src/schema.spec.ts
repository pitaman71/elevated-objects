import { ToString, generate } from './typescript';
import { Node as SchemaNode } from './schema';

describe('Typescript code generator', () => {
    for(let decl of ['boolean', 'function', 'number', 'string', 'bigint', 'symbol']) {
        it(`generates scalar type ${decl} correctly`, () => {
            const code = new ToString();
            generate(code, { schemaNode: decl });
            expect(code._result).toMatch(decl);
        });
    }
    for(let decl of [['boolean'], ['function'], ['number'], ['string'], ['bigint'], ['symbol']]) {
        it(`generates array type ${decl} correctly`, () => {
            const code = new ToString();
            generate(code, { schemaNode: decl });
            expect(code._result).toMatch(new RegExp(decl[0]+'\\s*\\[\\]'));
        });
    }
    let decl = { on: 'boolean', min: 'number', max: 'number', text: 'string' };
    it(`generates aggregate type ${decl} correctly`, () => {
        const code = new ToString();
        generate(code, { schemaNode: decl });
        expect(code._result).toMatch('{on: boolean; min: number; max: number; text: string; }');
    });
})
