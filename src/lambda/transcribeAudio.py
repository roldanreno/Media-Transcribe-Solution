import boto3
import datetime
import glob
import json
import logging
import os
import random
import uuid
import urllib.parse

from botocore.client import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info('Loading function')

def handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    # print (json.dumps(event))
    
    # ID
    assetID = 'prefix_' + str(uuid.uuid4())
    # Get the object from the event and show its content type
    sourceBucket = event['Records'][0]['s3']['bucket']['name']
    logger.info(sourceBucket)
    sourceKey = event['Records'][0]['s3']['object']['key']
    logger.info(sourceKey)
    sourceS3 = 's3://'+ sourceBucket + '/'
    fullSourceS3 = 's3://'+ sourceBucket + '/' + sourceKey
    logger.info('full: ' + fullSourceS3)
    destinationS3 = os.environ['DESTINATION']
    logger.info(destinationS3)
    region = os.environ['REGION']
    statusCode = 200
    
    transcribe = boto3.client('transcribe')
    
    try:
      response = transcribe.start_transcription_job(
        TranscriptionJobName=assetID,
        LanguageCode='en-US',
        MediaSampleRateHertz=48000,
        MediaFormat='mp3',
        Media={
            'MediaFileUri': fullSourceS3
        },
        OutputBucketName=destinationS3,
        OutputKey=assetID)
      '''Settings={
          'VocabularyName': 'string',
          'ShowSpeakerLabels': True|False,
          'MaxSpeakerLabels': 123,
          'ChannelIdentification': True|False,
          'ShowAlternatives': True|False,
          'MaxAlternatives': 123,
          'VocabularyFilterName': 'string',
          'VocabularyFilterMethod': 'remove'|'mask'|'tag'
      },
      ModelSettings={
          'LanguageModelName': 'string'
      },
      JobExecutionSettings={
          'AllowDeferredExecution': True|False,
          'DataAccessRoleArn': 'string'
      },
      ContentRedaction={
          'RedactionType': 'PII',
          'RedactionOutput': 'redacted'|'redacted_and_unredacted',
          'PiiEntityTypes': [
              'BANK_ACCOUNT_NUMBER'|'BANK_ROUTING'|'CREDIT_DEBIT_NUMBER'|'CREDIT_DEBIT_CVV'|'CREDIT_DEBIT_EXPIRY'|'PIN'|'EMAIL'|'ADDRESS'|'NAME'|'PHONE'|'SSN'|'ALL',
          ]
      },
      IdentifyLanguage=True|False,
      IdentifyMultipleLanguages=True|False,
      LanguageOptions=[
          'af-ZA'|'ar-AE'|'ar-SA'|'da-DK'|'de-CH'|'de-DE'|'en-AB'|'en-AU'|'en-GB'|'en-IE'|'en-IN'|'en-US'|'en-WL'|'es-ES'|'es-US'|'fa-IR'|'fr-CA'|'fr-FR'|'he-IL'|'hi-IN'|'id-ID'|'it-IT'|'ja-JP'|'ko-KR'|'ms-MY'|'nl-NL'|'pt-BR'|'pt-PT'|'ru-RU'|'ta-IN'|'te-IN'|'tr-TR'|'zh-CN'|'zh-TW'|'th-TH'|'en-ZA'|'en-NZ'|'vi-VN'|'sv-SE',
      ],
      Subtitles={
          'Formats': [
              'vtt'|'srt',
          ],
          'OutputStartIndex': 123
      },
      Tags=[
          {
              'Key': 'string',
              'Value': 'string'
          },
      ],
      LanguageIdSettings={
          'string': {
              'VocabularyName': 'string',
              'VocabularyFilterName': 'string',
              'LanguageModelName': 'string'
          }
      },
      ToxicityDetection=[
          {
              'ToxicityCategories': [
                  'ALL',
              ]
          },
      ]
      '''
  
    except Exception as e:
      print ('Exception: %s' % e)
      statusCode = 500
      raise
    
    finally:
      return {
        'statusCode': statusCode,
        'body': json.dumps('Ready!'),
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
      }