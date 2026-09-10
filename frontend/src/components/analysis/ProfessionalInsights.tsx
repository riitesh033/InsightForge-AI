import {
  AlertTriangle,
  CheckCircle2,
  Info,
  Lightbulb,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import type {
  ProfessionalInsight,
  InsightPriority,
} from "@/services/analysis";


interface ProfessionalInsightsProps {
  insights: ProfessionalInsight[];
}


function getPriorityStyles(
  priority: InsightPriority
) {
  switch (priority) {
    case "Critical":
      return {
        badge:
          "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300",
        icon:
          "text-red-600 dark:text-red-400",
      };

    case "High":
      return {
        badge:
          "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900 dark:bg-orange-950 dark:text-orange-300",
        icon:
          "text-orange-600 dark:text-orange-400",
      };

    case "Medium":
      return {
        badge:
          "border-yellow-200 bg-yellow-50 text-yellow-700 dark:border-yellow-900 dark:bg-yellow-950 dark:text-yellow-300",
        icon:
          "text-yellow-600 dark:text-yellow-400",
      };

    default:
      return {
        badge:
          "border-green-200 bg-green-50 text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-300",
        icon:
          "text-green-600 dark:text-green-400",
      };
  }
}


function getPriorityIcon(
  priority: InsightPriority
) {
  switch (priority) {
    case "Critical":
      return ShieldAlert;

    case "High":
      return AlertTriangle;

    case "Medium":
      return Info;

    default:
      return CheckCircle2;
  }
}


function getCategoryIcon(
  category: string
) {
  const normalized =
    category.toLowerCase();

  if (normalized.includes("relationship")) {
    return TrendingUp;
  }

  if (normalized.includes("anomaly")) {
    return AlertTriangle;
  }

  if (normalized.includes("statistics")) {
    return TrendingDown;
  }

  if (normalized.includes("quality")) {
    return ShieldAlert;
  }

  return Lightbulb;
}


export default function ProfessionalInsights({
  insights,
}: ProfessionalInsightsProps) {

  if (!insights.length) {
    return (
      <section
        className="
          rounded-2xl
          border
          border-border
          bg-card
          p-6
          shadow-sm
        "
      >
        <div
          className="
            flex
            items-center
            gap-3
          "
        >
          <div
            className="
              flex
              h-10
              w-10
              items-center
              justify-center
              rounded-lg
              bg-primary/10
              text-primary
            "
          >
            <Lightbulb size={20} />
          </div>

          <div>
            <h2 className="text-lg font-semibold">
              Professional Insights
            </h2>

            <p className="text-sm text-muted-foreground">
              No significant findings were generated
              from the verified analysis.
            </p>
          </div>
        </div>
      </section>
    );
  }


  return (
    <section
      className="
        rounded-2xl
        border
        border-border
        bg-card
        shadow-sm
      "
    >

      {/* Header */}

      <div
        className="
          flex
          items-start
          gap-3
          border-b
          border-border
          p-6
        "
      >

        <div
          className="
            flex
            h-10
            w-10
            shrink-0
            items-center
            justify-center
            rounded-lg
            bg-primary/10
            text-primary
          "
        >
          <Lightbulb size={20} />
        </div>

        <div>

          <h2 className="text-lg font-semibold">
            Professional Insights
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Evidence-based findings generated from
            the verified dataset analysis.
          </p>

        </div>

      </div>


      {/* Insights */}

      <div className="divide-y divide-border">

        {insights.map(
          (insight, index) => {

            const priorityStyles =
              getPriorityStyles(
                insight.priority
              );

            const PriorityIcon =
              getPriorityIcon(
                insight.priority
              );

            const CategoryIcon =
              getCategoryIcon(
                insight.category
              );

            return (
              <article
                key={`${insight.title}-${index}`}
                className="p-6"
              >

                {/* Insight Header */}

                <div
                  className="
                    flex
                    flex-col
                    gap-4
                    lg:flex-row
                    lg:items-start
                    lg:justify-between
                  "
                >

                  <div className="flex gap-3">

                    <div
                      className="
                        flex
                        h-9
                        w-9
                        shrink-0
                        items-center
                        justify-center
                        rounded-lg
                        bg-muted
                      "
                    >
                      <CategoryIcon
                        size={18}
                      />
                    </div>

                    <div>

                      <div
                        className="
                          flex
                          flex-wrap
                          items-center
                          gap-2
                        "
                      >

                        <h3
                          className="
                            text-base
                            font-semibold
                          "
                        >
                          {insight.title}
                        </h3>

                        <span
                          className={`
                            inline-flex
                            items-center
                            gap-1
                            rounded-full
                            border
                            px-2.5
                            py-1
                            text-xs
                            font-medium
                            ${priorityStyles.badge}
                          `}
                        >
                          <PriorityIcon
                            size={12}
                          />

                          {insight.priority}
                        </span>

                      </div>

                      <p
                        className="
                          mt-1
                          text-xs
                          text-muted-foreground
                        "
                      >
                        {insight.category}
                        {" · "}
                        Confidence: {insight.confidence}
                      </p>

                    </div>

                  </div>

                </div>


                {/* Finding */}

                <div className="mt-5">

                  <p
                    className="
                      text-sm
                      font-semibold
                    "
                  >
                    Finding
                  </p>

                  <p
                    className="
                      mt-1
                      text-sm
                      leading-6
                      text-muted-foreground
                    "
                  >
                    {insight.finding}
                  </p>

                </div>


                {/* Evidence */}

                {insight.evidence.length > 0 && (
                  <div className="mt-5">

                    <p
                      className="
                        text-sm
                        font-semibold
                      "
                    >
                      Evidence
                    </p>

                    <div
                      className="
                        mt-2
                        grid
                        gap-3
                        sm:grid-cols-2
                        lg:grid-cols-3
                      "
                    >

                      {insight.evidence.map(
                        (evidence, evidenceIndex) => (
                          <div
                            key={evidenceIndex}
                            className="
                              rounded-lg
                              border
                              border-border
                              bg-muted/30
                              p-3
                            "
                          >

                            <p
                              className="
                                text-xs
                                text-muted-foreground
                              "
                            >
                              {evidence.metric}
                            </p>

                            <p
                              className="
                                mt-1
                                text-sm
                                font-semibold
                              "
                            >
                              {evidence.value}
                            </p>

                            {evidence.context && (
                              <p
                                className="
                                  mt-1
                                  text-xs
                                  text-muted-foreground
                                "
                              >
                                {evidence.context}
                              </p>
                            )}

                          </div>
                        )
                      )}

                    </div>

                  </div>
                )}


                {/* Interpretation */}

                <div className="mt-5">

                  <p
                    className="
                      text-sm
                      font-semibold
                    "
                  >
                    Interpretation
                  </p>

                  <p
                    className="
                      mt-1
                      text-sm
                      leading-6
                      text-muted-foreground
                    "
                  >
                    {insight.interpretation}
                  </p>

                </div>


                {/* Potential Impact */}

                <div className="mt-5">

                  <p
                    className="
                      text-sm
                      font-semibold
                    "
                  >
                    Potential Impact
                  </p>

                  <p
                    className="
                      mt-1
                      text-sm
                      leading-6
                      text-muted-foreground
                    "
                  >
                    {insight.potential_impact}
                  </p>

                </div>


                {/* Recommended Action */}

                <div
                  className="
                    mt-5
                    rounded-xl
                    border
                    border-primary/20
                    bg-primary/5
                    p-4
                  "
                >

                  <div
                    className="
                      flex
                      items-start
                      gap-3
                    "
                  >

                    <Lightbulb
                      size={18}
                      className="
                        mt-0.5
                        shrink-0
                        text-primary
                      "
                    />

                    <div>

                      <p
                        className="
                          text-sm
                          font-semibold
                        "
                      >
                        Recommended Action
                      </p>

                      <p
                        className="
                          mt-1
                          text-sm
                          leading-6
                          text-muted-foreground
                        "
                      >
                        {insight.recommended_action}
                      </p>

                    </div>

                  </div>

                </div>

              </article>
            );
          }
        )}

      </div>

    </section>
  );
}