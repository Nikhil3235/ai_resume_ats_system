import io
import mimetypes
try:
    import magic
except ImportError:
    magic = None
from typing import Tuple, Optional

import pdfplumber
from docx import Document
import PyPDF2

from backend.utils.file_utils import(
    FileParsingError, 
    TextExtractionError, 
    FileUploadError, 
    log_error, 
    log_warning, 
    log_info, 
    with_fallback
)

from backend.core.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB, 
    SUPPORTED_MIME_TYPES
)

class FileParsingError(Exception):
    pass

class FileValidationError(Exception):
    pass

def validate_file(file_data: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
    file_size_bytes = len(file_data)
    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = file_size_bytes / (1024 * 1024)
        return False, (
            f'File size ({size_mb:.2f} MB) exceeds the maximum of {MAX_FILE_SIZE_MB} MB. '
            'Please upload a smaller file or compress your resume.'
        ), None

    if file_size_bytes == 0:
        return False, 'Uploaded file is empty. Please check the file and try again.', None

    # Step 1: Check magic bytes directly (foolproof across Android, iOS, Windows, Mac)
    short_type = None
    if file_data.startswith(b'%PDF'):
        short_type = 'pdf'
    elif file_data.startswith(b'PK\x03\x04'):
        short_type = 'docx'
    elif file_data.startswith(b'\xd0\xcf\x11\xe0'):
        short_type = 'doc'

    # Step 2: Check filename extension (case-insensitive)
    if not short_type:
        fname_lower = (filename or '').lower()
        if fname_lower.endswith('.pdf'):
            short_type = 'pdf'
        elif fname_lower.endswith('.docx'):
            short_type = 'docx'
        elif fname_lower.endswith('.doc'):
            short_type = 'doc'

    # Step 3: Check MIME types if magic bytes and extension didn't resolve
    if not short_type:
        mime_type = None
        if magic:
            try:
                mime_type = magic.from_buffer(file_data, mime=True)
            except Exception:
                pass
        if not mime_type:
            guessed, _ = mimetypes.guess_type(filename)
            mime_type = guessed or 'application/octet-stream'

        short_type = SUPPORTED_MIME_TYPES.get(mime_type)

    if not short_type:
        return False, (
            f'Unsupported file format for "{filename}". '
            'Please upload a valid PDF or Word (.docx) document.'
        ), None

    return True, '', short_type

def _extract_pdf_hyperlinks(file_data: bytes) -> str:
    urls = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        if getattr(reader, 'is_encrypted', False):
            try:
                reader.decrypt('')
            except Exception:
                pass
        for page in reader.pages:
            if '/Annots' not in page:
                continue
            for annot_ref in page['/Annots']:
                try:
                    annot = annot_ref.get_object()
                    if annot.get('/Subtype') != '/Link':
                        continue
                    action = annot.get('/A', {})
                    uri = action.get('/URI', '')
                    if uri and isinstance(uri, (str, bytes)):
                        if isinstance(uri, bytes):
                            uri = uri.decode('utf-8', errors='ignore')
                        uri = uri.strip()
                        if uri.startswith('http'):
                            urls.append(uri)
                except Exception:
                    pass
    except Exception:
        pass
    return '\n'.join(urls)


def _extract_pdf_with_pdfplumber(file_data: bytes) -> str:
    text = ''
    try:
        pdf_ctx = pdfplumber.open(io.BytesIO(file_data), password='')
    except Exception:
        pdf_ctx = pdfplumber.open(io.BytesIO(file_data))

    with pdf_ctx as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True)
            if not page_text or not page_text.strip():
                page_text = page.extract_text()
            # Fallback 1: word-by-word extraction for non-standard character spacings
            if not page_text or not page_text.strip():
                words = page.extract_words()
                if words:
                    page_text = ' '.join(w.get('text', '') for w in words if w.get('text'))
            # Fallback 2: table extraction if resume is structured in tables
            if not page_text or not page_text.strip():
                tables = page.extract_tables() or []
                t_lines = []
                for table in tables:
                    for row in table:
                        row_vals = [str(c).strip() for c in row if c and str(c).strip()]
                        if row_vals:
                            t_lines.append(' | '.join(row_vals))
                if t_lines:
                    page_text = '\n'.join(t_lines)

            if page_text and page_text.strip():
                text += page_text + '\n'

    hyperlinks = _extract_pdf_hyperlinks(file_data)
    if hyperlinks:
        text = text.strip() + '\n' + hyperlinks

    if not text.strip():
        raise TextExtractionError(
            'pdfplumber extracted no text',
            user_message='No text could be extracted from the PDF.'
        )

    return text.strip()


def _extract_pdf_with_pdfminer(file_data: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        text = pdfminer_extract_text(io.BytesIO(file_data), password='')
        if not text or not text.strip():
            text = pdfminer_extract_text(io.BytesIO(file_data))
        if text and len(text.strip()) > 10:
            hyperlinks = _extract_pdf_hyperlinks(file_data)
            if hyperlinks:
                text = text.strip() + '\n' + hyperlinks
            return text.strip()
    except Exception as exc:
        log_warning(f'pdfminer extraction failed: {exc}', context='resume_parser')
    raise TextExtractionError(
        'pdfminer extracted no text',
        user_message='No text could be extracted from the PDF.'
    )


def _extract_pdf_with_pypdf2(file_data: bytes) -> str:
    text = ''
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
    if getattr(pdf_reader, 'is_encrypted', False):
        try:
            pdf_reader.decrypt('')
        except Exception:
            try:
                pdf_reader.decrypt(b'')
            except Exception:
                pass

    for page in pdf_reader.pages:
        page_text = page.extract_text(orientations=(0, 90, 180, 270))
        if not page_text or not page_text.strip():
            page_text = page.extract_text()
        # Visitor fallback to capture raw operands
        if not page_text or not page_text.strip():
            chunks = []
            def visitor_fn(t, cm, tm, font_dict, font_size):
                if t and t.strip():
                    chunks.append(t.strip())
            try:
                page.extract_text(visitor_text=visitor_fn)
                if chunks:
                    page_text = ' '.join(chunks)
            except Exception:
                pass

        if page_text and page_text.strip():
            text += page_text + '\n'

    hyperlinks = _extract_pdf_hyperlinks(file_data)
    if hyperlinks:
        text = text.strip() + '\n' + hyperlinks

    if not text.strip():
        raise TextExtractionError(
            'PyPDF2 extracted no text',
            user_message='No text could be extracted from the PDF.'
        )

    return text.strip()


def _extract_pdf_raw_stream_text(file_data: bytes) -> str:
    import re
    chunks = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        if getattr(reader, 'is_encrypted', False):
            try:
                reader.decrypt('')
            except Exception:
                pass
        for page in reader.pages:
            try:
                contents = page.get_contents()
                if contents:
                    raw_data = contents.get_data() if hasattr(contents, 'get_data') else bytes(contents)
                    matches = re.findall(rb'\(([^()]{2,})\)', raw_data)
                    for m in matches:
                        try:
                            s = m.decode('utf-8', errors='ignore').strip()
                            if len(s) > 1 and any(c.isalnum() for c in s):
                                chunks.append(s)
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass

    result = ' '.join(chunks).strip()
    if len(result) > 20:
        return result
    raise TextExtractionError(
        'Raw stream extraction found insufficient text',
        user_message='No text could be extracted from raw PDF streams.'
    )


def extract_text_from_pdf(file_data: bytes) -> str:
    extraction_methods = [
        ('pdfplumber', _extract_pdf_with_pdfplumber),
        ('pdfminer', _extract_pdf_with_pdfminer),
        ('PyPDF2', _extract_pdf_with_pypdf2),
        ('raw_stream', _extract_pdf_raw_stream_text),
    ]

    last_error = None
    for name, method in extraction_methods:
        try:
            extracted = method(file_data)
            if extracted and len(extracted.strip()) > 10:
                log_info(f'PDF extraction succeeded using {name} ({len(extracted)} chars)', context='resume_parser')
                return extracted
        except Exception as e:
            last_error = e
            log_warning(f'PDF extraction with {name} failed: {e}', context='resume_parser')

    log_error(last_error, context='extract_text_from_pdf')
    raise FileParsingError(
        'Failed to extract selectable text from this PDF. '
        'The file appears to be a scanned image or photo without embedded text. '
        'Please ensure you upload an ATS-friendly PDF exported with text from Microsoft Word, Google Docs, or Canva.'
    )
    

def extract_text_from_docx(file_data: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_data))
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text)

        text = '\n'.join(text_parts)

        if not text.strip():
            raise FileParsingError(
                'No text could be extracted from the document. '
                'The document may be empty or corrupted.'
            )
        
        try:
            for rel in doc.part.rels.values():
                if 'hyperlink' in rel.reltype.lower():
                    url = rel._target
                    if isinstance(url, str) and url.startswith('http'):
                        text += '\n' + url
        except Exception:
            pass

        log_info(f'Extracted {len(text)} chars from DOCX', context='resume_parser')
        return text.strip()

    except FileParsingError:
        raise   # Re-raise unchanged — don't wrap in another FileParsingError

    except Exception as e:
        log_error(e, context='extract_text_from_docx')
        raise FileParsingError(
            'Failed to extract text from DOCX. '
            'The document may be corrupted or in an unsupported format. '
            'Please try re-saving or converting to PDF.'
        ) from e

def extract_text_from_doc(file_data: bytes) -> str:
    raise FileParsingError(
        'Legacy .doc format is not supported. '
        'Please convert your document to .docx or .pdf and try again. '
        'You can convert using Microsoft Word, Google Docs, or online tools.'
    )

def extract_text(file_data:bytes, file_type:str)->str:
    if file_type=='pdf':
        return extract_text_from_pdf(file_data)
    elif file_type=='docx':
        return extract_text_from_docx(file_data)
    elif file_type=='doc':
        return extract_text_from_doc(file_data)
    else:
        raise FileValidationError(
            f'invalid file type: {file_type}. supported types are: pdf, docx and doc'


        )
    
def parse_resume_file(file_data: bytes, filename:str)->Tuple[str, dict]:
    log_info(f'parsing file :{filename}', context='parse_Resume_file')

    #phase01:validate file
    try:
        is_valid, error_msg, file_type=validate_file(file_data, filename)
        if not is_valid:
            log_warning(f'valiudation failed for file {filename}', context='parse_resume_file')
            raise FileValidationError(error_msg)
    
    except FileValidationError as e:
        raise 

    except Exception as e:
        log_error(e, context='parse_resume_file_validation')
        raise FileValidationError(
            'Could not validate the uploaded file. Please ensure it is a valid PDF or DOCX.'
        ) from e
    
    #phase02: extraction of file

    try:
        text = extract_text(file_data, file_type)
        log_info(f'Extracted {len(text)} chars from {filename}', context='parse_resume_file')

    except FileParsingError:
        raise   # Re-raise unchanged

    except Exception as e:
        log_error(e, context='parse_resume_file_extraction')
        raise FileParsingError(
            'An unexpected error occurred while processing the file. '
            'Please try again or contact support if the problem persists.'
        ) from e

    metadata = {
        'filename':        filename,
        'file_type':       file_type,
        'file_size_bytes': len(file_data),
        'text_length':     len(text),
        'success':         True,
    }
    return text, metadata