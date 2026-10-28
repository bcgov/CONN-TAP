-- A charge listed in both the TLS pricebook and the LTO list must get the same
-- TLS sub-category from each. Returns the charges where they disagree.

select
    pb.service_id_key,
    pb.sub_category_code as pricebook_sub_category,
    lto.sub_category_code as lto_sub_category
from {{ ref('stg_telus_pricebook_services') }} pb
join {{ ref('telus_tls_charge_descriptions') }} lto on upper(lto.charge_description) = pb.service_id_key
where pb.service_category_code = 'time_limited_services'
    and pb.sub_category_code is distinct from lto.sub_category_code
