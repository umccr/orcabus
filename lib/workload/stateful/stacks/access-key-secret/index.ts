import { SecretValue, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { AccessKey, AccessKeyStatus, PolicyStatement, User } from 'aws-cdk-lib/aws-iam';
import { ISecret, Secret } from 'aws-cdk-lib/aws-secretsmanager';

/**
 * Props for the user access key stack.
 */
export type AccessKeySecretStackProps = {
  /**
   * Name of the secret to store the access tokens.
   */
  secretName: string;
  /**
   * The name of the user.
   */
  userName: string;
  /**
   * The policies to add to the user.
   */
  policies: PolicyStatement[];
};

/**
 * This component creates long-lived user access tokens inside secrets manager. This is used to authorize actions like
 * creating long-lived pre-signed URLs that can last up to 7 days.
 */
export class AccessKeySecret extends Stack {
  private readonly _secret: ISecret;

  constructor(scope: Construct, id: string, props: StackProps & AccessKeySecretStackProps) {
    super(scope, id, props);

    // Create a new user with the required policies.
    const user = new User(this, 'User', {
      userName: props.userName,
    });
    props.policies.forEach((policy) => user.addToPolicy(policy));

    const accessKey = new AccessKey(this, 'AccessKey', {
      user,
      status: AccessKeyStatus.ACTIVE,
    });

    this._secret = new Secret(this, 'Secret', {
      secretName: props.secretName,
      description: 'Contains an access key for an IAM user to perform long-lived actions',
      secretObjectValue: {
        accessKeyId: SecretValue.unsafePlainText(accessKey.accessKeyId),
        secretAccessKey: accessKey.secretAccessKey,
      },
    });
  }

  /**
   * Return the created secret.
   */
  public get secret(): ISecret {
    return this._secret;
  }
}
