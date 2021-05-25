import { Serializable } from './serialization';
import { Builder, Factory } from './construction';
import { Visitor } from './traversal';

export class Reader<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    builder: Builder<ExpectedType>;
    json: any;
    obj: ExpectedType|undefined;
    refs: { [key:string]: { [key:string]: any } };
    is_ref: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(builder: Builder<ExpectedType>, json: any, refs?: { [key:string]: { [key:string]: any } }) {
        this.builder = builder
        this.json = json;
        this.refs = refs ? refs : {};
        this.is_ref = false;
    }

    jsonPreview(): string {
        return(JSON.stringify(this.json).substr(0,80));
    }

    begin(obj: ExpectedType, parentPropName?: string) {
        // Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next
        if(!this.obj) {
            this.obj = obj;
        }
        const className = this.builder.getClassSpec();
        if(!this.refs.hasOwnProperty(className)) {
            this.refs[className] = {};
        }
        const by_id = this.refs[className];
        if(this.json.hasOwnProperty('__id__')) {
            if(by_id.hasOwnProperty(this.json['__id__'])) {
                this.obj = <ExpectedType>by_id[this.json['__id__']];
                this.is_ref = true;
            } else {
                by_id[this.json['__id__']] = this.obj;
            }
        }
    }

    end(obj:ExpectedType) {
        //Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
    }

    owner(target: ExpectedType, ownerPropName: string): void {}

    verbatim<DataType>(
        target: any, 
        propName: string,
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void,
        getPropNames: () => Array<string>                
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        setValue(target, this.json);
    }    

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if(!this.json) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(propName)) {
            const newValue = (typeof(this.json[propName]) === 'string')  && fromString ? fromString(this.json[propName]) : this.json[propName];
            target[propName] = newValue;
        }
    }    

    scalar<ElementType extends Serializable>(
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)
        if(!this.json) {
            target[propName] = undefined;
        } else if(this.json.hasOwnProperty(propName)) {            
            const item = this.json[propName];
            const reader = new Reader<ElementType>(this.builder.getPeer(item), item, this.refs);
            reader.read();
            if(reader.obj) {
                target[propName] = reader.obj;
            }
        }
    }

    array<ElementType extends Serializable>(
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(!this.json) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(propName)) {     
            const propValue = this.json[propName];            
            const newValue = propValue.map((item: any) => {
                const reader = new Reader<ElementType>(this.builder.getPeer(item), item, this.refs);
                reader.read();
                return(reader.obj);
            }).filter((item: ElementType|undefined): item is ElementType => !!item);
            target[propName] = newValue;
        }
    }

    map<ElementType extends Serializable>(
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(!this.json) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(propName)) {     
            const propValue = this.json[propName];            
            const newValue = Object.getOwnPropertyNames(propValue).reduce((newValue: any, key: string) => {
                const item = propValue[key];
                const reader = new Reader<ElementType>(this.builder.getPeer(item), item, this.refs);
                reader.read();
                if(reader.obj !== undefined) {
                    return { ... newValue, [key]: reader.obj};
                }
            }, {});
            target[propName] = newValue;
        }
    }

    read(
        classSpec_?: string
    ): any {
        const classSpec = 
            this.json && this.json.hasOwnProperty('__class__') ? this.json['__class__'] : classSpec_;

        if(!this.json) {
            this.obj = undefined;
        } else if(classSpec && this.factory.hasClass(classSpec)) {
            const newObject = <ExpectedType>this.factory.make(classSpec);
            newObject.marshal(this);
            this.obj = <ExpectedType>newObject;
            return newObject;
        } else {
            throw new Error(`Cannot construct object by reading JSON: ${this.jsonPreview()}`);
        }
    }
}

export class Writer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    builder: Builder<ExpectedType>;
    obj:ExpectedType;
    json: any;
    refs: { [key:string]: any[] };
    is_ref?: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(builder: Builder<ExpectedType>, obj: ExpectedType, refs?: { [key:string]: object[] }) {
        this.builder = builder;
        this.obj = obj;
        this.refs = refs ? refs : {};
    }

    begin(obj: ExpectedType, parentPropName?: string) {
        // Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next"""
        this.json = {};
        
        const classSpec = obj.getClassSpec();
        if(!this.refs.hasOwnProperty(classSpec)) {
            this.refs[classSpec] = [];
        }
        this.json['__class__'] = classSpec;
        if(!classSpec) {
            throw new Error(`Cannot find class name for ${typeof obj} with builders ${Object.getOwnPropertyNames(this.factory.specToBuilder)}`);
        }
        if(this.is_ref === undefined) {
            const ref_index = this.refs[classSpec].indexOf(obj);
            if(ref_index >= 0) {
                this.is_ref = true;
            } else {
                this.is_ref = false;
                this.refs[classSpec] = [ ... this.refs[classSpec], obj ];
            }        
        }
        const ident = this.refs[classSpec].indexOf(obj).toString();
        this.json['__id__'] = ident;
        this.json['__is_ref__'] = this.is_ref;
    }

    end(obj: ExpectedType) {
    }

    owner(target: ExpectedType, ownerPropName: string): void {}

    verbatim<DataType>(
        target: any, 
        propName: string,
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void,
        getPropNames: () => Array<string>                
    ): void {
        this.json = getValue(target);
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        if(target[propName] !== undefined && !this.is_ref) {
            this.json[propName] = target[propName];
        }
    }

    scalar<ElementType extends Serializable>(
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if(this.is_ref) return;
        if(target.hasOwnPropertyName(propName)) {
            const writer = new Writer<ElementType>(target[propName], this.factory, this.refs);
            writer.write();
            this.json[propName] = writer.json;
        }
    }

    array<ElementType extends Serializable>(
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(this.is_ref) return;
        if(target.hasOwnPropertyName(propName)) {
            this.json[propName] = target[propName].map((item: ElementType) => {
                const writer = new Writer<ElementType>(item, this.factory, this.refs);
                writer.write();
                return writer.json;
            }).filter((json:any) => !!json);
        }
    }

    map<ElementType extends Serializable>(
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(this.is_ref) return;
        if(target.hasOwnPropertyName(propName)) {
            this.json[propName] = target[propName].reduce((newValue: any, item: ElementType) => {
                const writer = new Writer<ElementType>(item, this.factory, this.refs);
                writer.write();
                return { ... newValue, [propName]: writer.json };
            }, {});
        }
    }

    write(): any {
        if(!!this.json) {
            // pass
        } else if(this.obj instanceof Serializable) {
            this.obj.marshal(this);
        } else {
            this.json = this.obj;
        }
        return this.json;
    }
}

export function toJSON(factory: Factory, obj: any, path?: any[]): any {
    const usePath = path || [];
    if(obj instanceof Serializable) {
        const writer = new Writer<any>(obj, factory, {});
        writer.write();
        return writer.json;
    } else if(Array.isArray(obj)) {
        const result = obj.map((item: any, index: number) => toJSON(factory, item, [ ...usePath, index]));
        return result;
    } else if(obj === Object(obj)) {
        const result = Object.getOwnPropertyNames(obj).reduce((result: any, propName: string) => {
            result[propName] = toJSON(factory, obj[propName], [ ...usePath, propName]);
            return result;
        }, {});
        return result;
    } else {
        return obj;
    }
}

export function fromJSON(factory: Factory, json: any): any {
    if(json && json.hasOwnProperty('__class__') && factory.hasClass(json['__class__'])) {
        const reader = new Reader<any>(factory.getBuilder(json), json, {}); 
        reader.read();
        return reader.obj;
    } else if(Array.isArray(json)) {
        return json.map((item: any) => fromJSON(factory, item));
    } else if(json === Object(json)) {
        return Object.getOwnPropertyNames(json).reduce((result: any, propName: string) => {
            result[propName] = fromJSON(factory, json[propName]);
            return result;
        }, {});
    } else {
        return json;
    }
}

export function toString(factory: Factory, obj: any): string {
    return JSON.stringify(toJSON(factory, obj, []));
}

export function fromString(factory: Factory, text: string) {
    return fromJSON(factory, JSON.parse(text));
}
