def id(ticker)
  case ticker
  when "Canadian Real Estate"
    return "CDN-REALESTATE"
  when "Commodities"
    return "COMMODITIES"
  when "U.S. Large-cap Equities"
    return "US-LGCAP-STOCK"
  when "U.S. Long-term Government Bonds"
    return "US-LONG-GOV-BOND"
  when "International Real Estate"
    return "INTL-REALESTATE"
  when "U.S. Real Estate"
    return "US-REALESTATE"
  when "U.S. Short-term Corporate Bonds"
    return "US-SHORT-CORP-BOND"
  when "Canadian Long-term Bonds"
    return "CDN-LONG-BOND"
  when "Canadian Short-term Bonds"
    return "CDN-SHORT-BOND"
  when "U.S. Small-cap Equities"
    return "US-SMCAP-STOCK"
  when "International Bonds"
    return "INTL-BOND"
  when "U.S. Short-term Government Bonds"
    return "US-SHORT-GOVT-BOND"
  when "U.S. Intermediate-term Corporate Bonds"
    return "US-MED-CORP-BOND"
  when "Canadian Equities"
    return "CDN-STOCK"
  when "U.S. Intermediate-term Government Bonds"
    return "US-MED-GOV-BOND"
  when "Emerging Markets Equities"
    return "EMERG-STOCK"
  when "U.S. Long-term Corporate Bonds"
    return "US-LONG-CORP-BOND"
  when "International Developed Equities (EAFE)"
    return "INTL-STOCK"
  else
    raise ticker
  end
end

etfs = []
Etf.all.each do |etf|
  security = etf.security
  etfs.push({
    ticker:       etf.ticker,
    description:  etf.description,
    security_id:  id(security.asset_class)
  })
end

assets = []
Security.all.each do |security|
  assets.push({
    id:                     id(security.asset_class),
    asset_class:            security.asset_class,
    asset_type:             security.asset_type,
    representative_ticker:  security.ticker,
  })
end
