import boto3
import os
import sys
import yaml
from botocore.exceptions import ClientError

stage = os.environ["STAGE"]

def get_record():
    with open ("serverless_vars.yml") as stream:
        try:
            content = (yaml.load(stream))
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

    return content[stage]['RECORD']


class Domain():
    def __init__(self, record):
        self.record = record


    def createDomain(self):
        client = boto3.client("apigateway")
        certArn = self.getCertARN()

        #Check if domain exist in apigateway
        if self.domainExist():
            print "Domain Already Exist"

        else:
            response = client.create_domain_name(
                        domainName=self.record,
                        certificateArn=certArn)
            print "creating Domain"
            self.distributionName = response['distributionDomainName']

        #update record irrespective of whether it exist or not
        response = self.updateRecord()
        print response


    def domainExist(self):
        client = boto3.client('apigateway')
        try:
            response = client.get_domain_name(
                domainName=self.record
                )
            self.distributionName = response['distributionDomainName']
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                print "Domain doesn't exist"
                return False
            else:
                print e
                sys.exit(1)

    def getRoute53HostedZoneId(self,client):
        response = client.list_hosted_zones_by_name()
        for domain in response['HostedZones']:
            if domain ['Name'][:-1] in self.record and not domain['Config']['PrivateZone'] :
                print "Hosted zone found " + domain['Name'] + ' ' + domain['Id']
                return domain['Id']
        print "Hostedzone not found"
        sys.exit(1)

    def updateRecord(self):
        client = boto3.client("route53")
        hostedzone = self.getRoute53HostedZoneId(client)

        response = client.change_resource_record_sets(
                        HostedZoneId=hostedzone,
                        ChangeBatch={
                            'Comment': 'API',
                            'Changes': [
                                    {
                                        'Action': 'UPSERT',
                                        'ResourceRecordSet': {
                                                'Name': self.record,
                                                'Type': 'A',

                                                'AliasTarget': {
                                                    'HostedZoneId': 'Z2FDTNDATAQYW2',
                                                    'DNSName': self.distributionName,
                                                    'EvaluateTargetHealth': False
                                                 },
                                                 }
                                        }
                                    ]
                                }
                            )
        return response

    def getCertARN(self):
        client = boto3.client('acm')
        response = client.list_certificates(CertificateStatuses=['ISSUED'])

        for cert in response['CertificateSummaryList']:
            certName = cert['DomainName']
            if certName[0]  == "*" :
                certName = certName[1:]

            if certName in self.record :
                return cert['CertificateArn']
        print "Certificate Not found. Exiting !"
        sys.exit(1)

def main():
    record = get_record()
    domain = Domain(record)
    domain.createDomain()
    return 0




if __name__ == '__main__':
    main()

    #print(lambda_handler({},{}))
