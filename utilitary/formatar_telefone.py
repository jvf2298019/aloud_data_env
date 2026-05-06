import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from phonenumbers.phonenumberutil import NumberParseException
import json
from typing import Dict, Any, Optional

def formatar_telefone(phone: str, default_region: str = 'BR') -> Dict[str, Any]:
    """
    Versão ROBUSTA usando python-phonenumbers (baseada na libphonenumber do Google).
    
    Args:
        phone: Número de telefone em qualquer formato
        default_region: Região padrão se não especificada (BR = Brasil)
    
    Returns:
        Dict com informações detalhadas do telefone
    """
    output = {
        'raw_phone_input': phone,
        'formatted_phone': '',
        'whatsapp_format': '',
        'isValid': False,
        'type': 'Invalid',
        'ddd': None,
        'ddi': None,
        'region': None,
        'carrier': None,
        'location': None,
        'timezone': None,
        'number_type': None
    }
    
    if not phone or not phone.strip():
        return output
    
    try:
        # Pré-processamento: Filtra caracteres não numéricos, exceto o "+"
        cleaned_phone = ''.join(c for c in phone.strip() if c.isdigit() or c == '+')

        if cleaned_phone.startswith('+'):
            cleaned_phone = cleaned_phone
        elif cleaned_phone.startswith('00') and len(cleaned_phone) > 2:
            cleaned_phone = '+' + cleaned_phone[2:]
        elif cleaned_phone.startswith('0') and not cleaned_phone.startswith('+') and len(cleaned_phone) > 10:
            cleaned_phone = '+' + cleaned_phone[1:]
        
        parsed_number = phonenumbers.parse(cleaned_phone, default_region)
        is_valid = phonenumbers.is_valid_number(parsed_number)
        is_possible = phonenumbers.is_possible_number(parsed_number)
        
        output['isValid'] = is_valid
        
        if not is_possible:
            output['type'] = 'Invalid'
            output['formatted_phone'] = phone
            output['whatsapp_format'] = phone
            return output
        
        output['ddi'] = str(parsed_number.country_code)
        output['region'] = phonenumbers.region_code_for_number(parsed_number)
        
        output['formatted_phone'] = phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164
        )
        output['whatsapp_format'] = output['formatted_phone']
        
        number_type = phonenumbers.number_type(parsed_number)
        type_mapping = {
            phonenumbers.PhoneNumberType.MOBILE: 'Mobile',
            phonenumbers.PhoneNumberType.FIXED_LINE: 'Fixed Line',
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: 'Fixed Line or Mobile',
            phonenumbers.PhoneNumberType.TOLL_FREE: 'Toll Free',
            phonenumbers.PhoneNumberType.PREMIUM_RATE: 'Premium Rate',
            phonenumbers.PhoneNumberType.VOIP: 'VoIP',
            phonenumbers.PhoneNumberType.UNKNOWN: 'Unknown'
        }
        output['number_type'] = type_mapping.get(number_type, 'Unknown')
        
        if output['region'] == 'BR':
            output['type'] = 'Nacional'
            national_number = str(parsed_number.national_number)
            if len(national_number) >= 10:
                output['ddd'] = national_number[:2]
                ddd_int = int(output['ddd']) if output['ddd'].isdigit() else 0
                if ddd_int > 28 and len(national_number) == 11 and national_number[2] == '9':
                    whatsapp_number = national_number[:2] + national_number[3:]
                    output['whatsapp_format'] = f"+55{whatsapp_number}"
                else:
                    output['whatsapp_format'] = f"+55{national_number}"
            try:
                output['carrier'] = carrier.name_for_number(parsed_number, 'pt')
                output['location'] = geocoder.description_for_number(parsed_number, 'pt')
                timezones = timezone.time_zones_for_number(parsed_number)
                output['timezone'] = list(timezones) if timezones else None
            except Exception:
                pass
        else:
            output['type'] = 'Internacional'
        
        if output['ddd'] and str(output['ddd']).isdigit():
            output['ddd'] = int(output['ddd'])
        if output['ddi'] and str(output['ddi']).isdigit():
            output['ddi'] = int(output['ddi'])
    except NumberParseException as e:
        output['type'] = 'Invalid'
        output['formatted_phone'] = phone
        output['whatsapp_format'] = phone
        output['error'] = str(e)
    except Exception as e:
        output['type'] = 'Invalid'
        output['formatted_phone'] = phone
        output['whatsapp_format'] = phone
        output['error'] = f"Unexpected error: {str(e)}"
    
    return output

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Formatador de telefone via phonenumbers')
    parser.add_argument('phone', help='Número de telefone para formatar')
    parser.add_argument('--region', default='BR', help='Região padrão para parsing (ex: BR, US, etc.)')
    parser.add_argument('--raw', action='store_true', help='Mostra o dict cru (não json)')
    args = parser.parse_args()

    result = formatar_telefone(args.phone, args.region)
    if args.raw:
        print(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))