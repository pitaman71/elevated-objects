import { Serializable } from './Serializable';
import { Visitor } from './Visitor';
import { Factory } from './Factory';
import * as Property from './Property';

export const logTags = {
    Reader: false
};

export class Initializer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    initializers: any[];
    obj?: ExpectedType;
    beginObject(obj: ExpectedType): void { this.obj = obj; }
    endObject(obj: ExpectedType): void {}

    constructor(...initializers: any[]) {
        this.initializers = initializers;
    }

    verbatim<DataType>(target: any, propName: string): void {
        const property = new Property.Primitive<DataType>(target, propName);
        const newValue = this.initializers.reduce(
            (result: any, initializer: any) => initializer || result
        , undefined);
        if(newValue !== undefined)
            property.setValue(newValue);
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        const property = new Property.Primitive<PropType>(target, propName);
        const newValue = this.initializers.reduce(
            (result: any, initializer: any) => initializer[propName] || result
        , undefined);
        if(newValue !== undefined) {
            const typedValue = (typeof(newValue) === 'string')  && fromString ? fromString(newValue) : newValue;
            property.setValue(typedValue);
        }
    }

    scalar<ObjectType extends Serializable>(target: any, propName: string): void {
        const property = new Property.Scalar<ObjectType>(target, propName);
        const newValues = this.initializers.filter(
            (initializer: any) => initializer[propName] !== undefined
        ).map((initializer: any) => initializer[propName]);
        if(newValues.length == 1) {
            return property.setValue(newValues[0]);
        } else if(newValues.length > 1) {
            return property.setValue(newValues[0].clone(... newValues));
        }
    }

    array<ElementType extends Serializable>(target: any, propName: string): void {
        const property = new Property.ArrayProp<ElementType>(target, propName);
        const hasProperty = this.initializers.filter(
            (initializer: any) => initializer[propName] !== undefined
        );
        const maxLength = hasProperty.reduce(
            (result: number, initializer: any) => 
                Math.max(initializer[propName].length, result)
        , 0);
        if(maxLength > 0) {
            const newArrayValue = [ ... Array(maxLength).keys() ].reduce(
                (arrayValue: ElementType[], index: number) => {
                    const longEnoughArrays = hasProperty.filter(
                        (initializer: any) => index < initializer[propName].length
                    );
                    const elementValues = longEnoughArrays.reduce(
                        (collected: ElementType[], initializer: any) => 
                        [ ... collected, initializer[propName][index]]
                    , []);
                    const elementValue: ElementType = elementValues.length > 0 && 
                        elementValues[0].clone(... elementValues);
                    return [ ... arrayValue, elementValue ];
                }
            , []);
            property.setValue(newArrayValue);
        }
    }

    init(target: ExpectedType): any {
        target.marshal(this);
    }
}

export class Reader<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    json: any;
    obj: ExpectedType|undefined;
    factory: Factory;
    refs: { [key:string]: { [key:string]: any } };
    is_ref: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(json: any, factory: Factory, refs?: { [key:string]: { [key:string]: any } }) {
        this.json = json;
        this.factory = factory;
        this.refs = refs ? refs : {};
        this.is_ref = false;
    }

    jsonPreview(): string {
        return(JSON.stringify(this.json).substr(0,80));
    }

    beginObject(obj: ExpectedType) {
        // Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next
        if(!this.obj) {
            this.obj = obj;
        }
        if(!this.json.hasOwnProperty('__class__')) {
            throw new Error(`Expected __class__ to be present in JSON. Properties included ${Object.keys(this.json)}`);
        }
        const class_name = this.json['__class__'];
        if(!this.refs.hasOwnProperty(class_name)) {
            this.refs[class_name] = {};
        }
        const by_id = this.refs[class_name];
        if(this.json.hasOwnProperty('__id__')) {
            if(by_id.hasOwnProperty(this.json['__id__'])) {
                this.obj = <ExpectedType>by_id[this.json['__id__']];
                this.is_ref = true;
            } else {
                by_id[this.json['__id__']] = this.obj;
            }
        }
    }

    endObject(obj:ExpectedType) {
        //Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
    }

    verbatim<DataType>(target: any, propName: string): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        const property = new Property.Primitive<DataType>(target, propName);
        if(!this.json) {
            throw new Error('No JSON here');
        } else {
            property.setValue(this.json);
        }
    }    

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        const property = new Property.Primitive<PropType>(target, propName);
        if(!this.json) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(property.propName)) {
            const newValue = (typeof(this.json[propName]) === 'string')  && fromString ? fromString(this.json[propName]) : this.json[propName];
            property.setValue(newValue);
        }
    }    

    scalar<ObjectType extends Serializable>(target: any, propName: string): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)
        const property = new Property.Scalar<ObjectType>(target, propName);
        if(!this.json) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(property.propName)) {            
            const reader = new Reader<ObjectType>(this.json[property.propName], this.factory, this.refs);
            reader.read();
            if(reader.obj) {
                property.setValue(reader.obj);
            }
        } else if (!this.is_ref) {
            if(logTags.Reader)
                console.log(`WARNING: While reading object of type ${this.obj?.getClassSpec()} property ${property.propName} is missing in JSON ${this.jsonPreview()}`);
        }
    }

    array<ElementType extends Serializable>(target: any, propName: string): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        const property = new Property.ArrayProp<ElementType>(target, propName);
        if(!this.json) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(property.propName)) {     
            const propValue = this.json[property.propName];            
            property.setValue(propValue.map((item: any) => {
                const reader = new Reader<ElementType>(item, this.factory, this.refs);
                reader.read();
                return(reader.obj);
            }).filter((item: ElementType|undefined): item is ElementType => !!item));
        } else if (!this.is_ref) {
            if(logTags.Reader)
                console.log(`WARNING: While reading object of type ${this.obj?.getClassSpec()} property ${property.propName} is missing in JSON ${this.jsonPreview()}`);
        }
    }

    read(): any {
        const klass = this.json['__class__']
        if(this.factory.hasClass(klass)) {
            const newObject = <ExpectedType>this.factory.instantiate(klass);
            newObject.marshal(this);
            this.obj = <ExpectedType>newObject;
            return newObject;
        } else {
            throw new Error(`Cannot construct object by reading JSON: ${this.jsonPreview()}`);
        }
    }
}

export class Writer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    obj:ExpectedType;
    json: any;
    factory: Factory;
    refs: { [key:string]: any[] };
    is_ref?: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(obj: ExpectedType, factory: Factory, refs?: { [key:string]: object[] }) {
        this.obj = obj;
        this.factory = factory;
        this.refs = refs ? refs : {};
    }

    beginObject(obj: ExpectedType) {
        // Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next"""
        this.json = {};
        
        const class_name = obj.getClassSpec();
        if(!this.refs.hasOwnProperty(class_name)) {
            this.refs[class_name] = [];
        }
        this.json['__class__'] = class_name;
        if(!class_name) {
            throw new Error(`Cannot find class name for ${typeof obj} with builders ${Object.getOwnPropertyNames(this.factory.specToBuilder)}`);
        }
        if(this.is_ref === undefined) {
            const ref_index = this.refs[class_name].indexOf(obj);
            if(ref_index >= 0) {
                this.is_ref = true;
            } else {
                this.is_ref = false;
                this.refs[class_name] = [ ... this.refs[class_name], obj ];
            }        
        }
        const ident = this.refs[class_name].indexOf(obj).toString();
        this.json['__id__'] = ident;
        this.json['__is_ref__'] = this.is_ref;
    }

    endObject(obj: ExpectedType) {
        // Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
        const class_name = obj.getClassSpec();
        const ident = this.json['__id__'];
    }

    verbatim<DataType>(target: any, propName: string): void {
        const property = new Property.Primitive<DataType>(target, propName);
        if(property.value && !this.is_ref) {
            this.json = property.value;
        }
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        const property = new Property.Primitive<PropType>(target, propName);
        if(property.value && !this.is_ref) {
            this.json[property.propName] = property.value;
        }
    }

    scalar<ObjectType extends Serializable>(target: any, propName: string): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)
        const property = new Property.Scalar<ObjectType>(target, propName);
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if(property.value && !this.is_ref) {
            const writer = new Writer<ObjectType>(property.value, this.factory, this.refs);
            writer.write();
            this.json[property.propName] = writer.json;
        }
    }

    array<ElementType extends Serializable>(target: any, propName: string): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        const property = new Property.ArrayProp<ElementType>(target, propName);
        if(property.value && !this.is_ref) {
            this.json[property.propName] = property.value.map((item: ElementType) => {
                const writer = new Writer<ElementType>(item, this.factory, this.refs);
                writer.write();
                return writer.json;
            }).filter((json:any) => !!json);
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
