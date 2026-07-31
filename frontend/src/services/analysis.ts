import api from "./api";

export interface Analysis {

    id:number;
    dataset_id:number;
    summary:any;
    summary_text:string;
    quality_score:number;
    column_info:any[];
    statistics:any;
    missing_values:any;
    duplicates:any;
    correlations:any;
    outliers:any;
}

export async function getAnalysis(
    datasetId:number
){

    const response = await api.get(
        `/api/v1/analysis/${datasetId}`
    );

    return response.data as Analysis;
}