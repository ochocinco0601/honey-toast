// Negative control - constructs that must NOT be read as emission sites.
// A match here is a regression in the emission rules' receiver binding.

class NotEmission {

    void notLogging() {
        // An `error` method on something that is not a logger. An unbound receiver,
        // `$X.error(...)`, matches all of these, and each one reads on a fact base as a
        // place the system emits something.
        validationResult.error("field is required");
        responseBuilder.error(400);
        parser.warn("deprecated syntax");

        // `info` on a domain object, same shape, same reason.
        buildReport.info("nothing to do");
    }
}
