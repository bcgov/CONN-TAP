-- A charge listed in both the TLS pricebook and the LTO list must get the same
-- sub-category from each. Returns the charges where they disagree.

select
    pb.service_id,
    pb.sub_category_code as pricebook_sub_category,
    lto.sub_category_code as lto_sub_category
from {{ ref('stg_telus_pricebook_services') }} pb
join {{ ref('telus_tls_charge_descriptions') }} lto on upper({{ clean_text('lto.charge_description', strip_punctuation=true) }}) = pb.service_id
where pb.service_category_code = 'time_limited_services'
    and pb.sub_category_code is distinct from lto.sub_category_code
