import { Node as SchemaNode } from './schema';
import { Error } from './parsing';
import * as Measurements from './measurements';
import { Point, Polygon } from 'geojson';

export type JSONValue = boolean | number | string | null | { [key: string]: JSONValue|undefined } | Array<JSONValue>;

export type Mass<X>  = X & { mass: number };

export type Transcoder<X,Y> = {
    from(x: X|null, options?: { onError?: (error: Error) => void }): Y|null;
    to(y: Y|null, options?: { onError?: (error: Error) => void }): X|null;
};

export type Format = {
    standard: string;
    definition:  string
};

/**
 * Abstract base for classes that model introspectable datatypes.
 */
export abstract class Domain<ValueType, FeatureKey=ValueType> {
    canonicalName: string;

    constructor(canonicalName: string) {
        this.canonicalName = canonicalName;
    }

    /** return the schema representation of this introspectable datatype */
    asSchema(): undefined|SchemaNode<any> { return undefined; }

    /** return the a description of this domain */
    asComment(): undefined|string[] { return undefined; }

    /** returns methods for parsing an object from JSON or printing an object to JSON */
    asJSON(): undefined|Transcoder<JSONValue, ValueType> { return undefined }

    asNumber(dimension?: Measurements.Dimension): undefined| Transcoder<number,ValueType> & {
        dimension: Measurements.Dimension;
    } { return undefined; }

    /** 
     * If this is an aggregate or aggregate-like datatype, 
     * calling this method will return a list of property names and a map 
     * from property names to subdomains 
     */
    asProperties(): undefined|Record<string, {
        name: string,
        domain: Domain<any>,
        required: boolean
    }> { return undefined }

    /** 
     * If this is an array or array-like datatype, 
     * calling this method will return a list of property names and a map 
     * from property names to subdomains 
     */
    asArray(): undefined|{
        indexDomains: () => undefined|Array<Domain<any>>;
        elementDomain: () => undefined|Domain<any> 
    } { return undefined }
    
    /** 
     * If this is an aggregate or aggregate-like datatype, 
     * calling this method will return a list of property names and a map 
     * from property names to subdomains 
     */
    asVariants(): undefined|{
        discKey: string,
        domain: Record<string, Domain<any>>
    } { return undefined }
    
    /**
     * If this domain has a countable number of legal values,
     * calling this method will return two methods for iterating
     * through that set of legal values in forward or backward order,
     * according to the domain's natural ordering of values.
     */
    asEnumeration(maxCount: number): undefined|{
        forward(): Generator<ValueType>;
        backward(): Generator<ValueType>;
    } { return undefined }

    /**
     * If the values of this domain may be mapped onto a feature
     * vector or embedding, calling this method returns will
     * select a function for feature vector or embedding and a 
     * feature distance metric for AI-compatible fuzzy search + matching.
     * 
     * The feature distance metric has range [0.0, 1.0] should reserve the value 1.0 for
     * a complete match (value equality). The value 0.0 should similarly be reserved for
     * a complete mismatch (nothing in common).
     * 
     * @param maxFeatureSize a number which limits the feature vector size
     */
    asFeature(maxFeatureSize: number): undefined|{
        /**
         * Call this function repeatedly across a collection of values to
         * build a histogram of matched and unmatched values and value parts
         * according to the feature vector/embedding.
         * 
         * @param value the next value to add to the characterization
         * @param options.featureMass a histogram of feature indices to cumulative mass
         * @param options.unclassifiedCount a count of values (and value parts, such as substrings, if applicable) that matched no feature
         */
        characterize(value: ValueType, options: { featureMass?: Map<FeatureKey, Mass<{ key: FeatureKey }>>, unclassified?: Map<ValueType, number> }): void;
        
        /**  
         * Convert a value in this domain to a feature vector/embedding as a
         * sparse array of feature objects comprising the feature index and weight, 
         * sorted in decreasing weight, where the weight is always a floating point number 
         * weight = 0.0 means no matches of any kind, and such features should be omitted by convention
         * if a non-empty set of non-overlapping proper substring matches are found, their weights are summed
         * a full pattern substring match has weight 1.0, with increasingly fuzzy matches decreasing towards 0.0
         * a full string exact match gets weight +Inf
         */
        to(value: ValueType): Map<FeatureKey, Mass<{ key: FeatureKey }>>,
        /**
         * Convert a feature vector/embedding to a finite set of weighted example values.
         * @param featureMass histogram of feature indices to mass
         * @param numSamples: maximum number of random samples to generate
         */
        from(featureMass: Map<FeatureKey, Mass<{ key: FeatureKey }>>, numSamples: number): Generator<Mass<{ value: ValueType }>>,
    } { return undefined }

    /**
     * If this domain has a string representation, calling this
     * method will return methods for converting a value to or
     * from string representation.
     * 
     * NOTE: by convention, if `format` is provided and the Domain
     * does not recognize the specific requested format, this method must 
     * return `undefined`. It should not coerce to a different format.
     * If `format` is not provided, this method may coerce to any known format.
     */
    abstract asString(format?: Format): undefined|Transcoder<string, ValueType>;

    /**
     * Compares the two provided values according to the domain's natural sort
     * order, if one exists.
     * @returns -1 if a is ordered before b
     * @returns 0 if a and b have the same position in the order (equivalent value)
     * @returns +1 if b is ordered before a
     * @returns undefined if the order of a and b cannot be determined
     */
    abstract cmp(a: ValueType, b:ValueType): undefined|-1|0|1;
}

export type getValueType<T> = T extends Domain<infer U> ? U : never;
