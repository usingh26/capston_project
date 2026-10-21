# Comparison: Function-Based vs Class-Based Design

## Function-Based Implementation

The function-based implementation organizes the application into separate functions, such as `read_file()`, `validate_data()`, and `create_report()`. Each function performs a specific task and passes data to the next function.

**Advantages:
- Simple to understand,suitable for small applications.
- Easy to test individual functions.
- Requires less code and fewer concepts.

**Limitations:
- Harder to maintain when application grows.
- Adding many validation can make the validation function more complex.

## Class-Based Implementation

The class-based implementation uses `PdfModuleComplianceAuditor` to manage the auditing process and a base `Validator` class with specialized validator classes for individual rules. It uses inheritance, instance and class attributes, methods, and dunder methods to organize the application.

**Advantages:
- Each validator have single responsibility, making ode easier to extend and maintain.
- Inheritance allows specific validators to share a common interface.
- The auditor stores configuration and validator objects, keeping related data and behavior together.

**Limitations:
- Need good at OOP.
- May introduce more code and structure than necessary for a small application.

## Conclusion

Both implementations perform the same core tasks: reading CSV or JSON manifests, validating records, calculating compliance metrics, and generating a JSON report.

The function-based design is straightforward and works well for smaller scripts. The class-based design provides a more extensible structure when the application needs additional validation rules or more complex behavior. For this project, implementing both approaches demonstrates how the same requirements can be solved using different programming styles.