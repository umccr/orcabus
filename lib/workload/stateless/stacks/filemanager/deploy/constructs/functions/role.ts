import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import { ManagedPolicy, PolicyStatement, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Duration } from 'aws-cdk-lib';

/**
 * Props for role.
 */
export type RoleProps = {
  /**
   * Use a pre-existing role.
   */
  role?: iam.Role,
  /**
   * The service principal assumed by the role if not using a pre-existing role.
   */
  servicePrincipal?: string,
  /**
   * The name of the role if not using a pre-existing role.
   */
  roleName?: string,
  /**
   * The description of the role if not using a pre-existing role.
   */
  roleDescription?: string,
};

/**
 * A construct for the oneshot API fargate task.
 */
export class Role extends Construct {
  readonly role: iam.Role;

  constructor(scope: Construct, id: string, props: RoleProps) {
    super(scope, id);

    if (props.role !== undefined) {
      this.role = props.role;
    } else if (props.servicePrincipal !== undefined) {
      this.role = new iam.Role(this, 'Role', {
        assumedBy: new ServicePrincipal(props.servicePrincipal),
        description: props.roleDescription,
        roleName: props.roleName,
        maxSessionDuration: Duration.hours(12),
      });
    } else {
      throw new Error('either a role or service principal must be provided');
    }
  }

  /**
   * Add an AWS managed policy to the function's role.
   */
  addAwsManagedPolicy(policyName: string) {
    this.role.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName(policyName));
  }

  /**
   * Add a customer managed policy to the function's role.
   */
  addCustomerManagedPolicy(policyName: string) {
    this.role.addManagedPolicy(ManagedPolicy.fromManagedPolicyName(this, 'Policy', policyName));
  }

  /**
   * Add a policy statement to this function's role.
   */
  addToPolicy(policyStatement: PolicyStatement) {
    this.role.addToPolicy(policyStatement);
  }

  /**
   * Add policies for 's3:List*' and 's3:Get*' on the buckets to this function's role.
   */
  addPoliciesForBuckets(buckets: string[], actions: string[]) {
    Role.formatPoliciesForBucket(buckets, actions).forEach((policy) => {
      this.addToPolicy(policy);
    });
  }

  /**
   * Get policy actions for fetching objects.
   */
  static getObjectVersionActions(): string[] {
    return ['s3:GetObjectVersion'];
  }

  /**
   * Get policy actions for versioned objects.
   */
  static getObjectActions(): string[] {
    return ['s3:ListBucket', 's3:GetObject'];
  }

  /**
   * Format a set of buckets and actions into policy statements.
   */
  static formatPoliciesForBucket(buckets: string[], actions: string[]): PolicyStatement[] {
    return buckets.map((bucket) => {
      return new PolicyStatement({
        actions,
        resources: [`arn:aws:s3:::${bucket}`, `arn:aws:s3:::${bucket}/*`],
      });
    });
  }

  /**
   * Get policy actions for using object tags.
   */
  static objectTaggingActions(): string[] {
    return [
      's3:GetObjectTagging',
      's3:GetObjectVersionTagging',
      's3:PutObjectTagging',
      's3:PutObjectVersionTagging',
    ];
  }
}