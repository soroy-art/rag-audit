# Clearing the workspace
rm(list=ls())

guideline_metadata = read.csv(file="../data/csv-pubmedpmco-set_painmanagement.csv", header = TRUE, stringsAsFactors = FALSE)

pmcids = guideline_metadata$PMCID
out_dir = "pmc_openaccess_xml"
pkg_dir = file.path(out_dir, "oa_packages")   # where paper tgz + extracted files go
overwrite = FALSE
sleep_sec = 0.34

if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)
if (!dir.exists(pkg_dir)) dir.create(pkg_dir, recursive = TRUE)

# normalize inputs like "PMCID:PMC12345", "PMC12345", or "12345"
norm_pmcid <- function(x) {
  if (is.na(x) || !nzchar(trimws(as.character(x)))) return(NA_character_)
  s <- trimws(as.character(x))
  s <- sub("^PMCID:\\s*", "", s, ignore.case = TRUE)
  if (!grepl("^PMC", s, ignore.case = TRUE)) {
    if (grepl("^[0-9]+$", s)) s <- paste0("PMC", s)
  }
  toupper(s)
}

# parse OA XML to get tgz link (prefers tgz if present)
extract_oa_tgz_href <- function(xml_raw) {
  txt <- rawToChar(xml_raw)
  doc <- xml2::read_xml(txt)
  node <- xml2::xml_find_first(doc, ".//link[translate(@format,'TGZ','tgz')='tgz']")
  if (inherits(node, "xml_missing")) return(NA_character_)
  href <- xml2::xml_attr(node, "href")
  if (is.na(href) || !nzchar(href)) return(NA_character_)
  href
}

# prefer https even if OA returns ftp
to_https_if_ftp <- function(href) {
  if (is.na(href)) return(NA_character_)
  sub("^ftp://ftp\\.ncbi\\.nlm\\.nih\\.gov/", "https://ftp.ncbi.nlm.nih.gov/", href)
}

pmcids_norm <- vapply(pmcids, norm_pmcid, character(1))
base <- "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"

results <- data.frame(
  pmcid = pmcids,
  pmcid_norm = pmcids_norm,
  oa_xml_path = NA_character_,
  tgz_url = NA_character_,
  tgz_path = NA_character_,
  extract_dir = NA_character_,
  status = NA_character_,
  http_status = NA_integer_,
  stringsAsFactors = FALSE
)

ua <- httr::user_agent("pmc-oa-downloader/1.0")

for (i in seq_along(pmcids_norm)) {
  pmcid <- pmcids_norm[i]
  
  if (is.na(pmcid)) {
    results$status[i] <- "missing_pmcid"
    next
  }
  
  # 1) Download OA response XML (oa.fcgi?id=PMCxxxx)
  out_xml <- file.path(out_dir, paste0(pmcid, "_oa.xml"))
  
  if (!file.exists(out_xml) || overwrite) {
    url <- paste0(base, "?id=", pmcid)
    print(url)
    
    resp <- tryCatch(httr::GET(url, ua), error = function(e) NULL)
    if (is.null(resp)) {
      results$status[i] <- "oa_query_failed"
      next
    }
    
    code <- httr::status_code(resp)
    results$http_status[i] <- code
    if (code != 200) {
      results$status[i] <- "oa_query_failed"
      next
    }
    
    bin <- httr::content(resp, as = "raw")
    writeBin(bin, out_xml)
  } else {
    results$http_status[i] <- 200L
    bin <- readBin(out_xml, what = "raw", n = file.info(out_xml)$size)
  }
  
  results$oa_xml_path[i] <- out_xml
  
  # 2) If OA says it's open access, extract tgz link and download the package
  href_ftp <- extract_oa_tgz_href(bin)
  tgz_url <- to_https_if_ftp(href_ftp)
  results$tgz_url[i] <- tgz_url
  
  if (is.na(tgz_url)) {
    results$status[i] <- "no_oa_package"
    Sys.sleep(sleep_sec)
    next
  }
  
  tgz_path <- file.path(pkg_dir, paste0(pmcid, ".tar.gz"))
  extract_dir <- file.path(pkg_dir, pmcid)
  
  results$tgz_path[i] <- tgz_path
  results$extract_dir[i] <- extract_dir
  
  # download tgz (paper package)
  if (!file.exists(tgz_path) || overwrite) {
    ok <- tryCatch({
      utils::download.file(tgz_url, destfile = tgz_path, mode = "wb", quiet = TRUE)
      TRUE
    }, error = function(e) FALSE)
    
    if (!ok || !file.exists(tgz_path)) {
      results$status[i] <- "tgz_download_failed"
      Sys.sleep(sleep_sec)
      next
    }
  }
  
  # extract tgz
  if (!dir.exists(extract_dir) || overwrite) {
    if (!dir.exists(extract_dir)) dir.create(extract_dir, recursive = TRUE)
    ok2 <- tryCatch({
      utils::untar(tgz_path, exdir = extract_dir)
      TRUE
    }, error = function(e) FALSE)
    
    if (!ok2) {
      results$status[i] <- "tgz_extract_failed"
      Sys.sleep(sleep_sec)
      next
    }
  }
  
  results$status[i] <- "ok"
  Sys.sleep(sleep_sec)
}
