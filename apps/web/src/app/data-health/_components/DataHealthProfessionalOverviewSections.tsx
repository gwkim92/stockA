import type {
  ProfessionalAnalysisNextAction,
  ProfessionalAnalysisQuality,
  ProfessionalRecommendationCoverageAudit,
} from "./dataHealthTypes";
import { DataHealthProfessionalNextActionSection } from "./DataHealthProfessionalNextActionSection";
import { DataHealthProfessionalQualitySection } from "./DataHealthProfessionalQualitySection";
import { DataHealthProfessionalRecommendationAuditSection } from "./DataHealthProfessionalRecommendationAuditSection";

type DataHealthProfessionalOverviewSectionsProps = {
  readonly professionalQuality: ProfessionalAnalysisQuality;
  readonly professionalRecommendationAudit: ProfessionalRecommendationCoverageAudit;
  readonly professionalNextAction: ProfessionalAnalysisNextAction;
};

export function DataHealthProfessionalOverviewSections({
  professionalQuality,
  professionalRecommendationAudit,
  professionalNextAction,
}: DataHealthProfessionalOverviewSectionsProps) {
  return (
    <>
      <DataHealthProfessionalQualitySection professionalQuality={professionalQuality} />
      <DataHealthProfessionalRecommendationAuditSection
        professionalRecommendationAudit={professionalRecommendationAudit}
      />
      <DataHealthProfessionalNextActionSection professionalNextAction={professionalNextAction} />
    </>
  );
}
