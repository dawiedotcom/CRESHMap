select 
	datazone, 
	"1km_eligib", 
	case when "1km_eligib" = 1
		then 'Eligible'
	    else 'Not Eligible' end 
    as eligib_label,
	"500m_prior",
	case when "500m_prior" = 1
		then 'High Priority'
	    else 'Low Priority' end 
    as prior_label
from 
	datazones_eligibility_priority;
