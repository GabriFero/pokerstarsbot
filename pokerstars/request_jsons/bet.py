bet_payload = {
    'credentials': {
        'channelId': 62,
        'channelType': 'ONLINE',
        'token': "",
        'accountCode': "",
    },
    'sportBetSlip': {
        'enableNewBindabilityLogic': True,
        'tradingSegment': {
            'offerId': 0,
            'brandId': 390,
        },
        'bonusSet': {
            'betType': 'ACCUMULATOR',
            'bonus': [
                {
                    'bonusType': 'INCREMENTAL_BONUS',
                    'bonusParameterList': [
                        {
                            'name': 'MIN_SHARE',
                            'type': 'DECIMAL',
                            'value': '1.24',
                        },
                        {
                            'name': 'BONUS_PERCENTAGE',
                            'type': 'DECIMAL',
                            'value': '1.04',
                        },
                        {
                            'name': 'DAY_NUM',
                            'type': 'INTEGER',
                            'value': '7',
                        },
                        {
                            'name': 'MIN_NUM_EVENT',
                            'type': 'INTEGER',
                            'value': '5',
                        },
                    ],
                },
            ],
        },
        'stakeAmount': 100,
        'payoutAmount': 133,
        'oddsChangeSetting': 0,  # static
        'variableStakeAmount': 0,  # static
        'legList': [
            {
                'competitionDescription': 'ITA Serie A',
                'competitionIconUrl': 'https://www.pokerstars.it/ns-images/icons/competition/Italia.svg',
                'competitionId': '209',
                'competitorList': '',  # static, already empty
                'eventDescription': 'Salernitana - Napoli',
                'eventId': 3061261,
                'eventTimestamp': '2023-11-04T14:00:00.000Z',
                'isFixed': False,
                'isLive': True,
                'legMax': 30,
                'legMin': 1,
                'legMultiple': 1,
                'marketAttributeId': 0,
                'marketDescription': 'ESITO FINALE 1X2',
                'marketId': '416014514',
                'marketTypeDescription': None,  # static
                'marketTypeId': 3,
                'multipla': 0,
                'odd': 133,
                'regulatorEventId': '33441-3286',
                'regulatorPredictionId': '',  # static, already empty
                'selectionDescription': '2',
                'selectionId': '3285161237',
                'selectionType': 3,
                'sportDescription': 'Calcio',
                'sportIconUrl': 'https://www.pokerstars.it/ns-images/icons/sport/calcio.svg',
                'sportId': 1,
                'marketSelfBindable': False,
            },
        ],
    },
    'ticketType': 'ACCUMULATOR',
}

bet_url = "https://betting.pokerstars.it/api/biglietto-common/sell/sellSportBet"

