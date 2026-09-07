import { ReviewInbox } from '@/components/review/ReviewInbox';
export const metadata = { title: '내 검토함' };
/** Deliberately independent of the company/source APIs. The app server is still required. */
export default function ResearchNotesPage() {
  return <ReviewInbox />;
}
