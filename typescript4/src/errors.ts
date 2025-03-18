/**
 * Interface for returning details about an error
 */
export interface Basic<Syndromes extends string> {
    kind: Syndromes,
    details?: string;
    stack?: Array<{
        file: string,
        line: number
    }>;
}
