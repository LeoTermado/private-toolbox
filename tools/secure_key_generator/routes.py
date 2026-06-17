"""Secure Key Generator blueprint.

Generates secrets locally and renders them straight into the response. Nothing
is uploaded, downloaded, saved, printed or logged — generated values live only
for the duration of the request.
"""
from flask import Blueprint, render_template, request, make_response

from . import service

bp = Blueprint('secure_key_generator', __name__, url_prefix='/security/key-generator')


def _render(opts, result=None, error=None):
    html = render_template(
        'secure_key_generator.html',
        opts=opts,
        result=result,
        error=error,
        presets=service.PRESETS,
        presets_json=service.presets_for_client(),
        limits=service.LIMITS,
        wordlist_size=service.WORDLIST_SIZE,
    )
    # This page can contain freshly generated secrets. Tell the browser (and any
    # intermediary) never to cache or store it, including the back/forward cache.
    resp = make_response(html)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp


@bp.route('/')
def index():
    return _render(dict(service.DEFAULTS))


@bp.route('/generate', methods=['POST'])
def generate():
    # Parse first so we can always re-render the form with the user's settings.
    try:
        opts = service.parse_options(request.form)
    except service.ValidationError as exc:
        return _render(dict(service.DEFAULTS), error=str(exc))

    try:
        service.validate_options(opts)
        values = service.generate(opts)
    except service.ValidationError as exc:
        return _render(opts, error=str(exc))
    except Exception:
        # Never let an unexpected error reach the debugger: its traceback page
        # would expose local variables, which at this point may hold generated
        # secrets. Re-render with a generic message and no detail.
        return _render(opts, error="Generation failed unexpectedly. Please adjust "
                                   "your settings and try again.")

    # Masked twins of every visible secret area. These let the page render fully
    # masked (server-side, before any JS runs) when "hide" mode is on, so the
    # real secret is never painted while hidden. The real values are still sent
    # (in `values` / `formats`) purely so the copy buttons copy the true value.
    masked_values = [service.mask_value(v) for v in values]
    var_name = opts["variable_name"]

    result = {
        "values": values,
        "masked_values": masked_values,
        "count": len(values),
        "entropy": service.estimate_entropy(opts),
        "formats": service.build_all_formats(values, var_name),
        "formats_masked": service.build_all_formats(masked_values, var_name),
        "selected_output": service.format_output(
            values, opts["output_template"], var_name),
        "masked_output": service.format_output(
            masked_values, opts["output_template"], var_name),
    }
    return _render(opts, result=result)
