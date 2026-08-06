import {
  FileDown,
} from "lucide-react";


interface Props {
  datasetId: number;
}


export default function ReportButton({
  datasetId,
}: Props) {


  function downloadReport() {

    window.open(
      `${import.meta.env.VITE_API_URL}/analysis/${datasetId}/report`,
      "_blank"
    );

  }


  return (

    <button
      onClick={downloadReport}
      className="flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-primary-foreground hover:opacity-90"
    >

      <FileDown
        className="h-5 w-5"
      />

      Generate Report

    </button>

  );

}