declare module "*.geojson" {
    const value: any;
    export default value;
}

declare module 'proj4' {
    var proj4: any;
    export = proj4;
}

// custom.d.ts
declare namespace JSX {
    interface IntrinsicElements {
        input: React.DetailedHTMLProps<React.InputHTMLAttributes<HTMLInputElement>, HTMLInputElement> & {
            webkitdirectory?: string;
        };
    }
}
