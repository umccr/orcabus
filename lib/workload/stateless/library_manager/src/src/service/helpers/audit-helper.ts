import { Client, Executor } from 'edgedb';
import { insertSystemAuditEvent, updateSystemAuditEvent } from '../../../dbschema/queries';
import * as interfaces from '../../../dbschema/interfaces';
import ActionOutcomeType = interfaces.audit.ActionOutcome;
import ActionType = interfaces.audit.ActionType;
import { Transaction } from 'edgedb/dist/transaction';

/**
 * A pattern that encapsulate the function with try-catch mechanism and audit entry for the action
 *
 * @param edgeDbClient
 * @param actionDescription
 * @param transFunc
 * @returns
 */
export const systemAuditEventPattern = async <T>(
  edgeDbClient: Client,
  actionCategory: ActionType = 'E',
  actionDescription: string,
  transFunc: (tx: Transaction) => Promise<T>
): Promise<T> => {
  const auditEventId = await startSystemAuditEvent(edgeDbClient, actionCategory, actionDescription);

  try {
    const transResult = await edgeDbClient.transaction(async (tx: Transaction) => {
      return await transFunc(tx);
    });
    await completeSystemAuditEvent(edgeDbClient, auditEventId, 'success', new Date(), transResult);
    return transResult;
  } catch (error) {
    const errorString = error instanceof Error ? error.message : String(error);

    await completeSystemAuditEvent(edgeDbClient, auditEventId, 'error', new Date(), {
      error: errorString,
    });

    throw error;
  }
};

/**
 * Start the entry for a system audit event.
 *
 * @param executor
 * @param actionCategory
 * @param actionDescription
 * @param details
 * @param inProgress
 * @param actionOutcome
 * @returns
 */
export const startSystemAuditEvent = async (
  executor: Executor,
  actionCategory: ActionType,
  actionDescription: string,
  details: any = { errorMessage: 'Audit entry not completed' },
  inProgress = true,
  actionOutcome: ActionOutcomeType = 'error'
): Promise<string> => {
  return (
    await insertSystemAuditEvent(executor, {
      actionCategory,
      actionDescription,
      actionOutcome,
      details,
      inProgress,
    })
  ).id;
};

/**
 *  Complete the audit entry made at the beginning
 *
 * @param executor
 * @param auditEventId
 * @param outcome
 * @param endDate
 * @param details
 */
export const completeSystemAuditEvent = async (
  executor: Executor,
  auditEventId: string,
  outcome: ActionOutcomeType,
  endDate: Date,
  details: any
): Promise<void> => {
  await updateSystemAuditEvent(executor, {
    auditDbId: auditEventId,
    actionOutcome: outcome,
    details,
    occurredDateTime: endDate,
    inProgress: false,
  });
};
