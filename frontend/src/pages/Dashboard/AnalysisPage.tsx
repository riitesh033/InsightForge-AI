import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Download,
  FileCheck2,
  Loader2,
  MessageSquare,
  Sparkles,
} from "lucide-react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  Dataset,
  getDatasets,
  previewCleaning,
  applyCleaning,
  downloadDatasetFile,
  DownloadFormat,
  CleaningResponse,
} from "@/services/dataset";

import { useAnalysis } from "@/hooks/useAnalysis";

import AnalysisStats from "@/components/analysis/AnalysisStats";
import QualityScore from "@/components/analysis/QualityScore";
import ColumnInfoTable from "@/components/analysis/ColumnInfoTable";
import MissingValuesChart from "@/components/analysis/MissingValuesChart";
import DuplicateCard from "@/components/analysis/DuplicateCard";
import CorrelationHeatmap from "@/components/analysis/CorrelationHeatmap";
import OutlierCard from "@/components/analysis/OutlierCard";
import AIInsights from "@/components/analysis/AIInsights";


export default function AnalysisPage() {
  const { datasetId } =
    useParams<{ datasetId: string }>();

  const navigate = useNavigate();

  const {
    data,
    loading,
    error,
  } = useAnalysis(datasetId);


  // ==========================================================
  // Dataset
  // ==========================================================

  const [dataset, setDataset] =
    useState<Dataset | null>(null);

  const [loadingDataset, setLoadingDataset] =
    useState(true);


  // ==========================================================
  // Download State
  // ==========================================================

  const [downloadFormat, setDownloadFormat] =
    useState<DownloadFormat>("pdf");

  const [downloading, setDownloading] =
    useState(false);

  const [downloadError, setDownloadError] =
    useState<string | null>(null);


  // ==========================================================
  // Cleaning State
  // ==========================================================

  const [cleaningData, setCleaningData] =
    useState<CleaningResponse | null>(null);

  const [cleaningLoading, setCleaningLoading] =
    useState(false);

  const [cleaningApplying, setCleaningApplying] =
    useState(false);

  const [cleaningError, setCleaningError] =
    useState<string | null>(null);

  const [cleaningApplied, setCleaningApplied] =
    useState(false);


  // ==========================================================
  // Load Dataset Information
  // ==========================================================

  useEffect(() => {
    if (!datasetId) {
      setLoadingDataset(false);
      return;
    }

    async function loadDataset() {
      try {
        setLoadingDataset(true);

        const response =
          await getDatasets();

        const foundDataset =
          response.items.find(
            (item) =>
              item.id === Number(datasetId)
          );

        setDataset(
          foundDataset ?? null
        );
      } catch (error) {
        console.error(
          "Failed to load dataset information:",
          error
        );

        setDataset(null);
      } finally {
        setLoadingDataset(false);
      }
    }

    loadDataset();
  }, [datasetId]);


  // ==========================================================
  // Preview Cleaning
  // ==========================================================

  async function handlePreviewCleaning() {
    if (!datasetId) {
      return;
    }

    try {
      setCleaningLoading(true);
      setCleaningError(null);
      setCleaningApplied(false);
      setDownloadError(null);
      setDownloadFormat("pdf");

      const response =
        await previewCleaning(
          Number(datasetId)
        );

      setCleaningData(response);

    } catch (error) {
      setCleaningError(
        error instanceof Error && 'response' in error 
          ? (error as any).response?.data?.detail ?? "Unable to generate cleaning preview."
          : error instanceof Error 
            ? error.message 
            : "Unable to generate cleaning preview."
      );

    } finally {
      setCleaningLoading(false);
    }
  }


  // ==========================================================
  // Apply Cleaning
  // ==========================================================

  async function handleApplyCleaning() {
    if (!datasetId || !cleaningData) {
      return;
    }

    if (
      cleaningData.preview.changes.length === 0
    ) {
      return;
    }

    try {
      setCleaningApplying(true);
      setCleaningError(null);

      const response =
        await applyCleaning(
          Number(datasetId)
        );

      setCleaningData(response);
      setCleaningApplied(true);

    } catch (error) {
      setCleaningError(
        error instanceof Error && 'response' in error 
          ? (error as any).response?.data?.detail ?? "Unable to clean the dataset."
          : error instanceof Error 
            ? error.message 
            : "Unable to clean the dataset."
      );

    } finally {
      setCleaningApplying(false);
    }
  }


  // ==========================================================
  // Unified Download
  // ==========================================================

  async function handleDownload() {
    if (!datasetId) {
      return;
    }

    if (
      downloadFormat !== "pdf" &&
      !cleaningApplied
    ) {
      setDownloadError(
        "Apply cleaning before downloading the cleaned dataset."
      );

      return;
    }

    try {
      setDownloading(true);
      setDownloadError(null);

      await downloadDatasetFile(
        Number(datasetId),
        downloadFormat
      );

    } catch (error) {
      setDownloadError(
        error instanceof Error && 'response' in error 
          ? (error as any).response?.data?.detail ?? "Unable to download the selected file."
          : error instanceof Error 
            ? error.message 
            : "Unable to download the selected file."
      );

    } finally {
      setDownloading(false);
    }
  }


  // ==========================================================
  // Loading
  // ==========================================================

  if (loading || loadingDataset) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">

          <Loader2
            size={32}
            className="mx-auto mb-3 animate-spin text-primary"
          />

          <p className="text-muted-foreground">
            Loading analysis...
          </p>

        </div>
      </div>
    );
  }


  // ==========================================================
  // Error
  // ==========================================================

  if (error) {
    return (
      <div className="space-y-4">

        <button
          onClick={() =>
            navigate("/dashboard/datasets")
          }
          className="
            inline-flex
            items-center
            gap-2
            text-sm
            font-medium
            text-muted-foreground
            transition
            hover:text-foreground
          "
        >
          <ArrowLeft size={16} />
          Back to Datasets
        </button>


        <div className="
          rounded-xl
          border
          border-red-200
          bg-red-50
          p-5
          text-red-600
          dark:border-red-900
          dark:bg-red-950
          dark:text-red-400
        ">
          {error}
        </div>

      </div>
    );
  }


  // ==========================================================
  // No Analysis
  // ==========================================================

  if (!data) {
    return (
      <div className="space-y-4">

        <button
          onClick={() =>
            navigate("/dashboard/datasets")
          }
          className="
            inline-flex
            items-center
            gap-2
            text-sm
            font-medium
            text-muted-foreground
            transition
            hover:text-foreground
          "
        >
          <ArrowLeft size={16} />
          Back to Datasets
        </button>


        <div className="
          rounded-xl
          border
          p-8
          text-center
        ">
          <h2 className="text-lg font-semibold">
            No analysis found
          </h2>

          <p className="mt-2 text-sm text-muted-foreground">
            This dataset does not have an analysis available yet.
          </p>
        </div>

      </div>
    );
  }


  // ==========================================================
  // Dataset Name
  // ==========================================================

  const datasetName =
    dataset?.original_filename ??
    `Dataset #${data.dataset_id}`;


  // ==========================================================
  // Cleaning Statistics
  // ==========================================================

  const cleaningPreview =
    cleaningData?.preview;

  // const totalOutliers =
  //   cleaningPreview
  //     ? Object.values(
  //         cleaningPreview.outliers_detected
  //       ).reduce(
  //         (total, count) =>
  //           total + count,
  //         0
  //       )
  //     : 0;

  const hasCleaningChanges =
    Boolean(
      cleaningPreview &&
      cleaningPreview.changes.length > 0
    );


  // ==========================================================
  // Main
  // ==========================================================

  return (
    <div className="space-y-8">

      {/* =====================================================
          Header
      ====================================================== */}

      <div className="space-y-5">

        {/* Back Button */}

        <button
          onClick={() =>
            navigate("/dashboard/datasets")
          }
          className="
            inline-flex
            items-center
            gap-2
            text-sm
            font-medium
            text-muted-foreground
            transition
            hover:text-foreground
          "
        >
          <ArrowLeft size={16} />
          Back to Datasets
        </button>


        {/* Header Content */}

        <div className="
          flex
          flex-col
          gap-5
          lg:flex-row
          lg:items-center
          lg:justify-between
        ">

          <div className="min-w-0">

            <p className="mb-2 text-sm font-medium text-primary">
              Dataset Analysis
            </p>

            <h1 className="
              truncate
              text-3xl
              font-bold
              tracking-tight
            ">
              {datasetName}
            </h1>

            <p className="mt-2 text-muted-foreground">
              AI-powered data quality report and analysis
            </p>

          </div>


          {/* Header Actions */}

          <div className="
            flex
            shrink-0
            flex-wrap
            items-center
            gap-3
          ">

            {/* AI Chat */}

            <button
              onClick={() =>
                navigate(
                  `/dashboard/ai-chat/${data.dataset_id}`
                )
              }
              className="
                inline-flex
                items-center
                gap-2
                rounded-lg
                border
                border-border
                bg-card
                px-4
                py-2.5
                text-sm
                font-medium
                text-foreground
                shadow-sm
                transition
                hover:bg-accent
              "
            >
              <MessageSquare size={17} />
              AI Chat
            </button>


            {/* Download Format */}

            <select
              value={downloadFormat}
              onChange={(event) =>
                setDownloadFormat(
                  event.target.value as DownloadFormat
                )
              }
              className="
                rounded-lg
                border
                border-border
                bg-card
                px-3
                py-2.5
                text-sm
                font-medium
                text-foreground
                outline-none
                transition
                focus:ring-2
                focus:ring-primary/30
              "
            >
              <option value="pdf">
                PDF Report
              </option>

              <option
                value="csv"
                disabled={!cleaningApplied}
              >
                CSV
                {!cleaningApplied
                  ? " — Apply Cleaning"
                  : ""}
              </option>

              <option
                value="xlsx"
                disabled={!cleaningApplied}
              >
                XLSX
                {!cleaningApplied
                  ? " — Apply Cleaning"
                  : ""}
              </option>
            </select>


            {/* Download */}

            <button
              onClick={handleDownload}
              disabled={
                downloading ||
                (
                  downloadFormat !== "pdf" &&
                  !cleaningApplied
                )
              }
              className="
                inline-flex
                items-center
                justify-center
                gap-2
                rounded-lg
                bg-primary
                px-4
                py-2.5
                text-sm
                font-medium
                text-primary-foreground
                transition
                hover:opacity-90
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >

              {downloading ? (
                <>
                  <Loader2
                    size={17}
                    className="animate-spin"
                  />

                  Downloading...
                </>
              ) : (
                <>
                  <Download size={17} />

                  Download
                </>
              )}

            </button>

          </div>

        </div>


        {/* Download Error */}

        {downloadError && (
          <div className="
            rounded-lg
            border
            border-red-200
            bg-red-50
            p-3
            text-sm
            text-red-600
            dark:border-red-900
            dark:bg-red-950
            dark:text-red-400
          ">
            {downloadError}
          </div>
        )}

      </div>


      {/* =====================================================
          Quality Score
      ====================================================== */}

      <QualityScore
        score={data.quality_score}
      />


      {/* =====================================================
          Data Cleaning
      ====================================================== */}

      <section className="
        overflow-hidden
        rounded-2xl
        border
        border-border
        bg-card
        shadow-sm
      ">

        {/* Cleaning Header */}

        <div className="
          flex
          flex-col
          gap-4
          border-b
          border-border
          p-6
          sm:flex-row
          sm:items-center
          sm:justify-between
        ">

          <div className="flex items-start gap-3">

            <div className="
              flex
              h-10
              w-10
              shrink-0
              items-center
              justify-center
              rounded-lg
              bg-primary/10
              text-primary
            ">
              <Sparkles size={20} />
            </div>

            <div>

              <h2 className="text-lg font-semibold">
                Data Cleaning
              </h2>

              <p className="mt-1 text-sm text-muted-foreground">
                Automatically fix safe data-quality issues
                without changing the original dataset.
              </p>

            </div>

          </div>


          {/* Preview Button */}

          {!cleaningData && (
            <button
              onClick={handlePreviewCleaning}
              disabled={cleaningLoading}
              className="
                inline-flex
                shrink-0
                items-center
                justify-center
                gap-2
                rounded-lg
                bg-primary
                px-4
                py-2.5
                text-sm
                font-medium
                text-primary-foreground
                transition
                hover:opacity-90
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >

              {cleaningLoading ? (
                <>
                  <Loader2
                    size={17}
                    className="animate-spin"
                  />

                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles size={17} />

                  Preview Cleaning
                </>
              )}

            </button>
          )}

        </div>


        {/* Cleaning Error */}

        {cleaningError && (
          <div className="
            mx-6
            mt-6
            rounded-lg
            border
            border-red-200
            bg-red-50
            p-4
            text-sm
            text-red-600
            dark:border-red-900
            dark:bg-red-950
            dark:text-red-400
          ">
            {cleaningError}
          </div>
        )}


        {/* Cleaning Preview */}

        {cleaningPreview && (
          <div className="space-y-6 p-6">

            {/* =================================================
                Cleaning Status
            ================================================== */}

            {cleaningApplied ? (
              <div className="
                flex
                items-start
                gap-3
                rounded-xl
                border
                border-primary/20
                bg-primary/5
                p-5
              ">

                <div className="
                  flex
                  h-10
                  w-10
                  shrink-0
                  items-center
                  justify-center
                  rounded-full
                  bg-primary/10
                  text-primary
                ">
                  <FileCheck2 size={20} />
                </div>

                <div className="min-w-0">

                  <p className="font-semibold">
                    Cleaned dataset created successfully
                  </p>

                  <p className="
                    mt-1
                    text-sm
                    text-muted-foreground
                  ">
                    Your original dataset remains unchanged.
                    The cleaned version is ready to download.
                  </p>

                  {cleaningData.cleaned_filename && (
                    <p className="
                      mt-2
                      break-all
                      text-sm
                      font-medium
                      text-primary
                    ">
                      {cleaningData.cleaned_filename}
                    </p>
                  )}

                </div>

              </div>
            ) : (
              <div className="
                rounded-xl
                border
                border-border
                bg-background
                p-4
              ">

                <div className="flex items-start gap-3">

                  <Sparkles
                    size={19}
                    className="
                      mt-0.5
                      shrink-0
                      text-primary
                    "
                  />

                  <div>

                    <p className="font-medium">
                      Cleaning preview ready
                    </p>

                    <p className="
                      mt-1
                      text-sm
                      text-muted-foreground
                    ">
                      Review the proposed changes below
                      before creating the cleaned dataset.
                    </p>

                  </div>

                </div>

              </div>
            )}


            {/* =================================================
                Summary
            ================================================== */}

            <div>

              <div className="mb-3">

                <h3 className="font-semibold">
                  Cleaning Summary
                </h3>

                <p className="
                  mt-1
                  text-sm
                  text-muted-foreground
                ">
                  What InsightForge found and what it can safely fix.
                </p>

              </div>


              <div className="
                grid
                gap-4
                sm:grid-cols-2
                lg:grid-cols-3
                xl:grid-cols-6
              ">

                {/* Rows */}

                <div className="
                  rounded-xl
                  border
                  border-border
                  bg-background
                  p-4
                ">

                  <p className="
                    text-xs
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  ">
                    Rows
                  </p>

                  <p className="mt-2 text-2xl font-bold">
                    {cleaningPreview.rows_after.toLocaleString()}
                  </p>

                  <p className="
                    mt-1
                    text-xs
                    text-muted-foreground
                  ">
                    {cleaningPreview.rows_before ===
                    cleaningPreview.rows_after
                      ? "No rows removed"
                      : `${(
                          cleaningPreview.rows_before -
                          cleaningPreview.rows_after
                        ).toLocaleString()} removed`}
                  </p>

                </div>


                {/* Missing Values */}

                <div className="
                  rounded-xl
                  border
                  border-border
                  bg-background
                  p-4
                ">

                  <p className="
                    text-xs
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  ">
                    Missing
                  </p>

                  <p className="mt-2 text-2xl font-bold">
                    {cleaningPreview.missing_values_after}
                  </p>

                  <p className="
                    mt-1
                    text-xs
                    text-muted-foreground
                  ">
                    {cleaningPreview.missing_values_before} before
                  </p>

                </div>


                {/* Missing Filled */}

                <div className="
                  rounded-xl
                  border
                  border-border
                  bg-background
                  p-4
                ">

                  <p className="
                    text-xs
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  ">
                    Filled
                  </p>

                  <p className="mt-2 text-2xl font-bold">
                    {cleaningPreview.missing_values_filled}
                  </p>

                  <p className="
                    mt-1
                    text-xs
                    text-muted-foreground
                  ">
                    missing values fixed
                  </p>

                </div>


                {/* Duplicates */}

                <div className="
                  rounded-xl
                  border
                  border-border
                  bg-background
                  p-4
                ">

                  <p className="
                    text-xs
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  ">
                    Duplicates
                  </p>

                  <p className="mt-2 text-2xl font-bold">
                    {cleaningPreview.duplicates_removed}
                  </p>

                  <p className="
                    mt-1
                    text-xs
                    text-muted-foreground
                  ">
                    rows removed
                  </p>

                </div>


                {/* Whitespace */}

                <div className="
                  rounded-xl
                  border
                  border-border
                  bg-background
                  p-4
                ">

                  <p className="
                    text-xs
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  ">
                    Whitespace
                  </p>

                  <p className="mt-2 text-2xl font-bold">
                    {cleaningPreview.whitespace_cleaned}
                  </p>

                  <p className="
                    mt-1
                    text-xs
                    text-muted-foreground
                  ">
                    values cleaned
                  </p>

                </div>


                {/* Empty Strings */}

                <div className="
                  rounded-xl
                  border
                  border-border
                  bg-background
                  p-4
                ">

                  <p className="
                    text-xs
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  ">
                    Empty Values
                  </p>

                  <p className="mt-2 text-2xl font-bold">
                    {cleaningPreview.empty_strings_replaced}
                  </p>

                  <p className="
                    mt-1
                    text-xs
                    text-muted-foreground
                  ">
                    converted to missing
                  </p>

                </div>

              </div>

            </div>


            {/* =================================================
                Proposed Changes
            ================================================== */}

            {hasCleaningChanges ? (
              <div>

                <div className="mb-3 flex items-start gap-2">

                  <CheckCircle2
                    size={19}
                    className="mt-0.5 shrink-0 text-primary"
                  />

                  <div>

                    <h3 className="font-semibold">
                      Proposed Changes
                    </h3>

                    <p className="
                      mt-1
                      text-sm
                      text-muted-foreground
                    ">
                      These changes are considered safe to apply automatically.
                    </p>

                  </div>

                </div>


                <div className="space-y-3">

                  {cleaningPreview.changes.map(
                    (change, index) => {

                      const actionLabel =
                        change.action
                          .replace(/_/g, " ")
                          .replace(
                            /^./,
                            (char: string) =>
                              char.toUpperCase()
                          );

                      return (
                        <div
                          key={`${change.action}-${change.column}-${index}`}
                          className="
                            rounded-xl
                            border
                            border-border
                            bg-background
                            p-4
                            transition
                            hover:border-primary/30
                          "
                        >

                          <div className="
                            flex
                            flex-col
                            gap-4
                            sm:flex-row
                            sm:items-center
                            sm:justify-between
                          ">

                            <div className="
                              flex
                              items-start
                              gap-3
                            ">

                              <div className="
                                mt-0.5
                                flex
                                h-8
                                w-8
                                shrink-0
                                items-center
                                justify-center
                                rounded-lg
                                bg-primary/10
                                text-primary
                              ">
                                <CheckCircle2 size={16} />
                              </div>

                              <div>

                                <p className="font-medium">
                                  {change.column ||
                                    "Dataset"}
                                </p>

                                <p className="
                                  mt-1
                                  text-sm
                                  text-muted-foreground
                                ">
                                  {actionLabel}
                                </p>

                              </div>

                            </div>


                            <div className="
                              rounded-lg
                              bg-muted
                              px-3
                              py-2
                              text-sm
                              font-semibold
                              sm:text-right
                            ">

                              {change.count}

                              <span className="
                                ml-1
                                font-normal
                                text-muted-foreground
                              ">
                                affected
                              </span>

                            </div>

                          </div>

                        </div>
                      );
                    }
                  )}

                </div>

              </div>
            ) : (
              <div className="
                flex
                items-start
                gap-3
                rounded-xl
                border
                border-border
                bg-background
                p-5
              ">

                <CheckCircle2
                  size={21}
                  className="
                    mt-0.5
                    shrink-0
                    text-primary
                  "
                />

                <div>

                  <p className="font-medium">
                    No automatic cleaning required
                  </p>

                  <p className="
                    mt-1
                    text-sm
                    text-muted-foreground
                  ">
                    Your dataset does not contain issues
                    that InsightForge can safely fix automatically.
                  </p>

                </div>

              </div>
            )}


            {/* =================================================
                Warnings
            ================================================== */}

            {cleaningPreview.warnings.length > 0 && (
              <div className="
                rounded-xl
                border
                border-yellow-200
                bg-yellow-50
                p-5
                dark:border-yellow-900
                dark:bg-yellow-950/40
              ">

                <div className="flex items-start gap-3">

                  <AlertTriangle
                    size={20}
                    className="
                      mt-0.5
                      shrink-0
                      text-yellow-600
                      dark:text-yellow-400
                    "
                  />

                  <div className="min-w-0">

                    <p className="
                      font-semibold
                      text-yellow-800
                      dark:text-yellow-300
                    ">
                      Cleaning warnings
                    </p>

                    <p className="
                      mt-1
                      text-sm
                      text-yellow-700
                      dark:text-yellow-400
                    ">
                      These issues were detected but were not
                      automatically changed.
                    </p>

                    <ul className="mt-3 space-y-2">

                      {cleaningPreview.warnings.map(
                        (warning, index) => (
                          <li
                            key={index}
                            className="
                              flex
                              items-start
                              gap-2
                              text-sm
                              text-yellow-700
                              dark:text-yellow-400
                            "
                          >
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-current" />

                            <span>
                              {warning}
                            </span>
                          </li>
                        )
                      )}

                    </ul>

                  </div>

                </div>

              </div>
            )}


            {/* =================================================
                Cleaning Actions
            ================================================== */}

            <div className="
              flex
              flex-col
              gap-4
              border-t
              border-border
              pt-6
              sm:flex-row
              sm:items-center
              sm:justify-between
            ">

              <div>

                {cleaningApplied ? (
                  <div className="
                    flex
                    items-start
                    gap-2
                    text-sm
                    font-medium
                    text-primary
                  ">

                    <CheckCircle2
                      size={18}
                      className="mt-0.5 shrink-0"
                    />

                    <div>

                      <p>
                        Cleaning completed
                      </p>

                      <p className="
                        mt-1
                        font-normal
                        text-muted-foreground
                      ">
                        Select CSV or XLSX above to download
                        the cleaned dataset.
                      </p>

                    </div>

                  </div>
                ) : (
                  <div>

                    <p className="
                      text-sm
                      font-medium
                    ">
                      Ready to apply
                    </p>

                    <p className="
                      mt-1
                      text-sm
                      text-muted-foreground
                    ">
                      The original dataset will not be modified.
                    </p>

                  </div>
                )}

              </div>


              {!cleaningApplied && (
                <button
                  onClick={handleApplyCleaning}
                  disabled={
                    cleaningApplying ||
                    !hasCleaningChanges
                  }
                  title={
                    !hasCleaningChanges
                      ? "There are no automatic changes to apply."
                      : undefined
                  }
                  className="
                    inline-flex
                    items-center
                    justify-center
                    gap-2
                    rounded-lg
                    bg-primary
                    px-5
                    py-2.5
                    text-sm
                    font-medium
                    text-primary-foreground
                    transition
                    hover:opacity-90
                    disabled:cursor-not-allowed
                    disabled:opacity-60
                  "
                >

                  {cleaningApplying ? (
                    <>
                      <Loader2
                        size={17}
                        className="animate-spin"
                      />

                      Cleaning...
                    </>
                  ) : (
                    <>
                      <Sparkles size={17} />

                      Apply Cleaning
                    </>
                  )}

                </button>
              )}

            </div>

          </div>
        )}

      </section>


      {/* =====================================================
          Statistics
      ====================================================== */}

      <AnalysisStats
        summary={data.summary}
        missingValues={data.missing_values}
        duplicates={data.duplicates}
      />


      {/* =====================================================
          Columns
      ====================================================== */}

      <ColumnInfoTable
        columnInfo={data.column_info}
        statistics={data.statistics}
      />


      {/* =====================================================
          Quality Charts
      ====================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">

        <MissingValuesChart
          missingValues={
            data.missing_values
          }
        />

        <DuplicateCard
          duplicates={
            data.duplicates
          }
        />

      </div>


      {/* =====================================================
          Correlation
      ====================================================== */}

      {data.correlations && (
        <CorrelationHeatmap
          correlations={
            data.correlations
          }
        />
      )}


      {/* =====================================================
          Outliers
      ====================================================== */}

      {data.outliers && (
        <OutlierCard
          outliers={
            data.outliers
          }
        />
      )}


      {/* =====================================================
          AI Summary
      ====================================================== */}

      <AIInsights
        summary={data.summary_text}
      />

    </div>
  );
}