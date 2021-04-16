import { Builder } from './Builder';
import { Serializable } from './Serializable';
import * as JSONMarshal from './JSONMarshal';

export class Factory {
    specToBuilder: { [key: string]: () => Builder<any> };
    constructor(builders: (() => Builder<any>)[] ) {
        this.specToBuilder = builders.reduce(
            (builders: { [key: string]: () => Builder<any> }, builder: () => Builder<any>) => {
                const tmp = builder();
                builders[tmp.classSpec] = builder;
                return builders;
        }, {});
    }
    
    hasClass(classSpec: any): boolean {
        return classSpec && this.specToBuilder.hasOwnProperty(classSpec.toString());
    }

    instantiate(classSpec: any): Serializable {
        return this.specToBuilder[classSpec.toString()]().make();
    }

    toString(obj: any): string {
        return JSON.stringify(this.toJSON(obj));
    }

    fromString(text: string): any {
        return this.fromJSON(JSON.parse(text));
    }

    toJSON(obj: any, path?: any[]): any {
        const usePath = path || [];
        if(obj instanceof Serializable) {
            //console.log(`toJSON<Serializable> BEGIN ${usePath} = <${typeof obj}>${obj}`);
            const writer = new JSONMarshal.Writer<any>(obj, this);
            writer.write();
            //console.log(`toJSON<Serializable> END   ${usePath}`);
            return writer.json;
        } else if(Array.isArray(obj)) {
            //console.log(`toJSON<Array> BEGIN ${usePath} = <${typeof obj}>${obj}`);
            const result = obj.map((item: any, index: number) => this.toJSON(item, [ ...usePath, index]));
            //console.log(`toJSON<Array> END   ${usePath}`);
            return result;
        } else if(obj === Object(obj)) {
            //console.log(`toJSON<Object> BEGIN ${usePath}`);
            const result = Object.getOwnPropertyNames(obj).reduce((result: any, propName: string) => {
                result[propName] = this.toJSON(obj[propName], [ ...usePath, propName]);
                return result;
            }, {});
            //console.log(`toJSON<Object> END   ${usePath}`);
            return result;
        } else {
            //console.log(`toJSON<any> BEGIN ${usePath}`);
            //console.log(`toJSON<any> END   ${usePath}`);
            return obj;
        }
    }

    fromJSON(json: any): any {
        if(this.hasClass(json['__class__'])) {
            const builder = this.specToBuilder[json['__class__']]();
            const reader = new JSONMarshal.Reader<any>(json, this); 
            reader.read();
            return reader.obj;
        } else if(Array.isArray(json)) {
            return json.map((item: any) => this.fromJSON(item));
        } else if(json === Object(json)) {
            return Object.getOwnPropertyNames(json).reduce((result: any, propName: string) => {
                result[propName] = this.fromJSON(json[propName]);
                return result;
            }, {});
        } else {
            return json;
        }
    }
}
