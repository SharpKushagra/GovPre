'use client';

import { ProposalReviewPage } from '@/features/proposal-review/ProposalReviewPage';

export default function ProposalReviewRoute({
    params,
}: {
    params: { proposalId: string };
}) {
    return <ProposalReviewPage proposalId={params.proposalId} />;
}
